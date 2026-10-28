"""
Transaction Service orchestrating natural language parsing,
categorization, database persistence, and user correction learning.
"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import date
from src.database import Database
from src.models import Transaction, ParsedExpense, LearnedMapping
from src.amount_parser import parse_natural_language_expenses
from src.categorizer import Categorizer


class TransactionService:
    def __init__(self, db: Optional[Database] = None, use_ollama: bool = True):
        self.db = db or Database()
        self.categorizer = Categorizer(db=self.db, use_ollama=use_ollama)

    def parse_and_categorize_input(self, raw_text: str, transaction_date: Optional[str] = None) -> List[ParsedExpense]:
        """
        Parses raw natural language text into one or more categorized expenses.
        """
        parsed_items = parse_natural_language_expenses(raw_text)
        results: List[ParsedExpense] = []

        target_date = transaction_date or date.today().isoformat()

        for item in parsed_items:
            categorized = self.categorizer.categorize(
                description=item["description"],
                amount=item["amount"],
                raw_amount_str=item["raw_amount_str"],
                source_text=item["source_text"],
            )
            categorized.transaction_date = target_date
            results.append(categorized)

        return results

    def save_parsed_expenses(self, parsed_expenses: List[ParsedExpense], payment_method: str = "UPI") -> List[int]:
        """
        Converts parsed expenses into transactions and commits them to SQLite.
        """
        transactions = [p.to_transaction(payment_method=payment_method) for p in parsed_expenses]
        return self.db.insert_transactions_batch(transactions)

    def add_transaction(self, transaction: Transaction) -> int:
        """Adds a single transaction."""
        return self.db.insert_transaction(transaction)

    def update_transaction(self, transaction_id: int, updates: Dict[str, Any], learn_correction: bool = True) -> bool:
        """
        Updates an existing transaction.
        If category is changed and learn_correction is True, saves a learned mapping so future entries benefit.
        """
        original = self.db.get_transaction(transaction_id)
        if not original:
            return False

        success = self.db.update_transaction(transaction_id, updates)
        if success and learn_correction and "category" in updates:
            new_cat = updates["category"]
            if new_cat != original.category:
                # Save learned mapping for this description and merchant
                self.db.save_learned_mapping(
                    normalized_description=original.description,
                    category=new_cat,
                    merchant=original.merchant
                )
        return success

    def delete_transaction(self, transaction_id: int) -> bool:
        """Deletes a transaction."""
        return self.db.delete_transaction(transaction_id)

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Fetches single transaction by ID."""
        return self.db.get_transaction(transaction_id)

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
        """Queries transactions with filters and ordering."""
        return self.db.get_transactions(
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type,
            search=search,
            limit=limit,
            offset=offset,
            order_by=order_by
        )

    def count_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        return self.db.count_transactions(
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type,
            search=search
        )

    def get_learned_mappings(self) -> List[LearnedMapping]:
        """Returns all user-learned category mappings."""
        return self.db.get_all_learned_mappings()

    def delete_learned_mapping(self, mapping_id: int) -> bool:
        """Deletes a user-learned mapping."""
        return self.db.delete_learned_mapping(mapping_id)

    def add_learned_mapping(self, description: str, category: str, merchant: Optional[str] = None) -> int:
        """Explicitly adds or updates a learned mapping."""
        return self.db.save_learned_mapping(description, category, merchant)
