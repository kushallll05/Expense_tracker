"""
SQLite Database Layer for AI Expense Tracker.
Handles schema initialization, indexing, transactions, and CRUD operations.
"""
import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from src.config import DB_PATH
from src.models import Transaction, Budget, LearnedMapping


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._memory_conn = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
            self._memory_conn.execute("PRAGMA foreign_keys = ON")
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:" and self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        """Initializes database tables and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Transactions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                category TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('expense', 'income')),
                transaction_date TEXT NOT NULL,
                payment_method TEXT DEFAULT 'UPI',
                merchant TEXT,
                source_text TEXT,
                confidence REAL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Budgets Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0),
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK(year >= 2000),
                UNIQUE(category, month, year)
            );
            """)

            # Learned Category Mappings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_description TEXT NOT NULL UNIQUE,
                merchant TEXT,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(transaction_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(transaction_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_my ON budgets(year, month);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_learned_desc ON learned_mappings(normalized_description);")

    # ==================== Transaction CRUD ====================

    def insert_transaction(self, t: Transaction) -> int:
        """Inserts a single transaction and returns its ID."""
        now = datetime.now().isoformat()
        created_at = t.created_at or now
        updated_at = t.updated_at or now

        query = """
        INSERT INTO transactions (
            description, amount, category, transaction_type, transaction_date,
            payment_method, merchant, source_text, confidence, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            t.description.strip(),
            float(t.amount),
            t.category.strip(),
            t.transaction_type.strip(),
            t.transaction_date,
            t.payment_method or "UPI",
            t.merchant.strip() if t.merchant else None,
            t.source_text.strip() if t.source_text else None,
            float(t.confidence),
            created_at,
            updated_at
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def insert_transactions_batch(self, transactions: List[Transaction]) -> List[int]:
        """Inserts multiple transactions inside a single database transaction."""
        now = datetime.now().isoformat()
        ids = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for t in transactions:
                created_at = t.created_at or now
                updated_at = t.updated_at or now
                params = (
                    t.description.strip(),
                    float(t.amount),
                    t.category.strip(),
                    t.transaction_type.strip(),
                    t.transaction_date,
                    t.payment_method or "UPI",
                    t.merchant.strip() if t.merchant else None,
                    t.source_text.strip() if t.source_text else None,
                    float(t.confidence),
                    created_at,
                    updated_at
                )
                cursor.execute("""
                INSERT INTO transactions (
                    description, amount, category, transaction_type, transaction_date,
                    payment_method, merchant, source_text, confidence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, params)
                ids.append(cursor.lastrowid)
        return ids

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Retrieves a single transaction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            if row:
                return Transaction(**dict(row))
            return None

    def update_transaction(self, transaction_id: int, updates: Dict[str, Any]) -> bool:
        """Updates specific fields of an existing transaction."""
        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()
        allowed_cols = {
            "description", "amount", "category", "transaction_type",
            "transaction_date", "payment_method", "merchant", "confidence", "updated_at"
        }
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_cols}
        if not filtered_updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values()) + [transaction_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE transactions SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int) -> bool:
        """Deletes a transaction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            return cursor.rowcount > 0

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "transaction_date DESC, id DESC"
    ) -> List[Transaction]:
        """Queries transactions with comprehensive filters and sorting."""
        clauses = []
        params = []

        if start_date:
            clauses.append("transaction_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("transaction_date <= ?")
            params.append(end_date)
        if category and category != "All":
            clauses.append("category = ?")
            params.append(category)
        if transaction_type and transaction_type != "All":
            clauses.append("transaction_type = ?")
            params.append(transaction_type)
        if search:
            search_pattern = f"%{search.strip()}%"
            clauses.append("(description LIKE ? OR merchant LIKE ? OR category LIKE ?)")
            params.extend([search_pattern, search_pattern, search_pattern])

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        # Validate order_by against SQL injection
        safe_orders = {
            "transaction_date DESC, id DESC": "transaction_date DESC, id DESC",
            "transaction_date ASC, id ASC": "transaction_date ASC, id ASC",
            "amount DESC": "amount DESC",
            "amount ASC": "amount ASC",
            "category ASC": "category ASC",
        }
        order_clause = safe_orders.get(order_by, "transaction_date DESC, id DESC")

        query = f"SELECT * FROM transactions {where_str} ORDER BY {order_clause}"
        if limit is not None:
            query += f" LIMIT {int(limit)}"
            if offset is not None:
                query += f" OFFSET {int(offset)}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [Transaction(**dict(row)) for row in cursor.fetchall()]

    def count_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        """Returns count of matching transactions."""
        clauses = []
        params = []

        if start_date:
            clauses.append("transaction_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("transaction_date <= ?")
            params.append(end_date)
        if category and category != "All":
            clauses.append("category = ?")
            params.append(category)
        if transaction_type and transaction_type != "All":
            clauses.append("transaction_type = ?")
            params.append(transaction_type)
        if search:
            search_pattern = f"%{search.strip()}%"
            clauses.append("(description LIKE ? OR merchant LIKE ? OR category LIKE ?)")
            params.extend([search_pattern, search_pattern, search_pattern])

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT COUNT(*) FROM transactions {where_str}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    # ==================== Budget CRUD ====================

    def set_budget(self, budget: Budget) -> int:
        """Inserts or updates a monthly category budget."""
        query = """
        INSERT INTO budgets (category, monthly_limit, month, year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(category, month, year) DO UPDATE SET
            monthly_limit = excluded.monthly_limit
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (budget.category, float(budget.monthly_limit), int(budget.month), int(budget.year)))
            return cursor.lastrowid

    def get_budgets(self, month: int, year: int) -> List[Budget]:
        """Gets all budgets for a given month and year."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM budgets WHERE month = ? AND year = ? ORDER BY category ASC",
                (month, year)
            )
            return [Budget(**dict(row)) for row in cursor.fetchall()]

    def get_budget_for_category(self, category: str, month: int, year: int) -> Optional[Budget]:
        """Gets budget for a specific category in a given month and year."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM budgets WHERE category = ? AND month = ? AND year = ?",
                (category, month, year)
            )
            row = cursor.fetchone()
            if row:
                return Budget(**dict(row))
            return None

    def delete_budget(self, budget_id: int) -> bool:
        """Deletes a budget entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            return cursor.rowcount > 0

    # ==================== Learned Category Mappings ====================

    def save_learned_mapping(self, normalized_description: str, category: str, merchant: Optional[str] = None) -> int:
        """Saves a user confirmed category correction for future automated use."""
        norm_desc = normalized_description.strip().lower()
        now = datetime.now().isoformat()
        query = """
        INSERT INTO learned_mappings (normalized_description, merchant, category, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(normalized_description) DO UPDATE SET
            category = excluded.category,
            merchant = excluded.merchant
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (norm_desc, merchant, category, now))
            return cursor.lastrowid

    def get_learned_mapping(self, normalized_description: str) -> Optional[LearnedMapping]:
        """Finds learned category mapping by normalized description."""
        norm_desc = normalized_description.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM learned_mappings WHERE normalized_description = ?",
                (norm_desc,)
            )
            row = cursor.fetchone()
            if row:
                return LearnedMapping(**dict(row))
            return None

    def get_all_learned_mappings(self) -> List[LearnedMapping]:
        """Retrieves all user learned mappings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_mappings ORDER BY created_at DESC")
            return [LearnedMapping(**dict(row)) for row in cursor.fetchall()]

    def delete_learned_mapping(self, mapping_id: int) -> bool:
        """Deletes a learned mapping."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM learned_mappings WHERE id = ?", (mapping_id,))
            return cursor.rowcount > 0
