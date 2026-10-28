"""
CSV Import / Export and Analytical Report Generation.
Includes duplicate detection, fuzzy column mapping, and report generators.
"""
import csv
import io
from typing import List, Dict, Any, Tuple
from datetime import datetime, date
import pandas as pd
from src.models import Transaction
from src.database import Database
from src.categorizer import Categorizer
from src.config import CURRENCY_SYMBOL


def export_transactions_to_csv(transactions: List[Transaction]) -> str:
    """Exports a list of transactions to a CSV formatted string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "date", "description", "amount", "category",
        "type", "payment_method", "merchant", "confidence"
    ])
    for t in transactions:
        writer.writerow([
            t.id or "",
            t.transaction_date,
            t.description,
            t.amount,
            t.category,
            t.transaction_type,
            t.payment_method or "UPI",
            t.merchant or "",
            t.confidence,
        ])
    return output.getvalue()


def import_transactions_from_csv(
    csv_file_data: str,
    db: Database,
    categorizer: Categorizer
) -> Dict[str, Any]:
    """
    Parses and imports transactions from CSV data.
    Detects duplicates based on (date, amount, normalized description).
    Auto-categorizes when category is missing.
    """
    imported = 0
    duplicates = 0
    errors = []

    # Read existing transactions to detect duplicates quickly
    existing = db.get_transactions()
    existing_fingerprints = {
        (t.transaction_date, round(float(t.amount), 2), t.description.strip().lower())
        for t in existing
    }

    try:
        reader = csv.DictReader(io.StringIO(csv_file_data))
        # Normalize header keys to lowercase
        if not reader.fieldnames:
            return {"imported": 0, "duplicates": 0, "errors": ["Empty or invalid CSV file."]}

        headers = {col.strip().lower(): col for col in reader.fieldnames}

        # Map common column aliases
        date_col = next((headers[k] for k in ["date", "transaction_date", "txn_date", "time"] if k in headers), None)
        amt_col = next((headers[k] for k in ["amount", "amt", "cost", "price", "value"] if k in headers), None)
        desc_col = next((headers[k] for k in ["description", "desc", "details", "narration", "title", "remarks"] if k in headers), None)
        cat_col = next((headers[k] for k in ["category", "cat", "tag"] if k in headers), None)
        type_col = next((headers[k] for k in ["type", "transaction_type", "txn_type"] if k in headers), None)
        merchant_col = next((headers[k] for k in ["merchant", "vendor", "payee"] if k in headers), None)
        pay_col = next((headers[k] for k in ["payment_method", "mode", "payment"] if k in headers), None)

        if not amt_col or not desc_col:
            return {
                "imported": 0,
                "duplicates": 0,
                "errors": ["CSV must contain at least 'amount' and 'description' columns."]
            }

        new_transactions: List[Transaction] = []

        for row_idx, row in enumerate(reader, start=2):
            raw_desc = (row.get(desc_col) or "").strip()
            raw_amt = (row.get(amt_col) or "").strip().replace(",", "")
            if not raw_desc or not raw_amt:
                continue

            try:
                amount = float(raw_amt)
                if amount <= 0:
                    continue
            except ValueError:
                errors.append(f"Row {row_idx}: Invalid numeric amount '{raw_amt}'.")
                continue

            # Date parsing
            tx_date = date.today().isoformat()
            if date_col and row.get(date_col):
                val = row[date_col].strip()
                try:
                    # Attempt ISO first or parse with pandas
                    parsed_dt = pd.to_datetime(val)
                    tx_date = parsed_dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

            # Check duplicate fingerprint
            fingerprint = (tx_date, round(amount, 2), raw_desc.lower())
            if fingerprint in existing_fingerprints:
                duplicates += 1
                continue

            # Category parsing or auto-categorization
            category = None
            if cat_col and row.get(cat_col):
                candidate_cat = row[cat_col].strip()
                if candidate_cat:
                    category = candidate_cat.title()

            merchant = (row.get(merchant_col) or "").strip() if merchant_col else None
            t_type = (row.get(type_col) or "expense").strip().lower()
            if t_type not in ("expense", "income"):
                t_type = "expense"

            confidence = 1.0
            if not category:
                classified = categorizer.categorize(raw_desc, amount)
                category = classified.category
                confidence = classified.confidence
                if not merchant:
                    merchant = classified.merchant

            t = Transaction(
                description=raw_desc,
                amount=amount,
                category=category,
                transaction_type=t_type,
                transaction_date=tx_date,
                payment_method=(row.get(pay_col) or "UPI").strip() if pay_col else "UPI",
                merchant=merchant,
                confidence=confidence,
            )
            new_transactions.append(t)
            existing_fingerprints.add(fingerprint)

        if new_transactions:
            db.insert_transactions_batch(new_transactions)
            imported = len(new_transactions)

    except Exception as e:
        errors.append(f"Fatal CSV parsing error: {str(e)}")

    return {
        "imported": imported,
        "duplicates": duplicates,
        "errors": errors
    }


def generate_markdown_report(
    metrics: Dict[str, Any],
    cat_df: pd.DataFrame,
    insights: List[Dict[str, Any]],
    date_range_label: str = "All Time"
) -> str:
    """Generates an executive Markdown financial summary report."""
    md = []
    md.append(f"# 📊 Financial Executive Report ({date_range_label})")
    md.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    md.append("## 1. Executive Summary")
    md.append("| Metric | Value |")
    md.append("| :--- | :--- |")
    md.append(f"| **Total Income** | {CURRENCY_SYMBOL}{metrics.get('total_income', 0.0):,.2f} |")
    md.append(f"| **Total Expenses** | {CURRENCY_SYMBOL}{metrics.get('total_expenses', 0.0):,.2f} |")
    md.append(f"| **Net Balance** | {CURRENCY_SYMBOL}{metrics.get('net_savings', 0.0):,.2f} |")
    md.append(f"| **Savings Rate** | {metrics.get('savings_rate', 0.0)}% |")
    md.append(f"| **Average Daily Expense** | {CURRENCY_SYMBOL}{metrics.get('avg_daily_expense', 0.0):,.2f} |")
    md.append(f"| **Largest Transaction** | {CURRENCY_SYMBOL}{metrics.get('largest_expense', 0.0):,.2f} ({metrics.get('largest_expense_desc', 'None')}) |")
    md.append(f"| **Total Transactions** | {metrics.get('total_transactions', 0)} |")
    md.append("\n")

    md.append("## 2. Category Spending Breakdown")
    if not cat_df.empty:
        md.append("| Category | Total Spent | Share | Txn Count |")
        md.append("| :--- | :--- | :--- | :--- |")
        for _, row in cat_df.iterrows():
            md.append(f"| {row['category']} | {CURRENCY_SYMBOL}{row['total_amount']:,.2f} | {row['percentage']}% | {row['count']} |")
    else:
        md.append("_No category data available._")
    md.append("\n")

    md.append("## 3. Financial Insights & Observations")
    if insights:
        for ins in insights:
            badge = f"**[{ins.get('tag', 'Fact')}]**"
            md.append(f"- {ins.get('icon', '🔹')} {badge} **{ins.get('title')}:** {ins.get('message')}")
    else:
        md.append("_No automated insights recorded for this period._")
    md.append("\n")

    return "\n".join(md)
