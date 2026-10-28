"""
Unit tests for CSV import/export and Financial Insights Generator.
"""
import pytest
from src.database import Database
from src.categorizer import Categorizer
from src.models import Transaction
from src.csv_manager import export_transactions_to_csv, import_transactions_from_csv, generate_markdown_report
from src.analytics import FinancialAnalytics
from src.budget_manager import BudgetManager
from src.insights import FinancialInsightsGenerator


@pytest.fixture
def env():
    db = Database(":memory:")
    cat = Categorizer(db=db, use_ollama=False)
    bm = BudgetManager(db)
    return db, cat, bm


def test_csv_export_and_import(env):
    db, cat, _ = env

    t1 = Transaction(description="Dosa", amount=150.0, category="Food", transaction_type="expense", transaction_date="2026-10-01")
    t2 = Transaction(description="Petrol", amount=500.0, category="Transport", transaction_type="expense", transaction_date="2026-10-02")
    db.insert_transactions_batch([t1, t2])

    # Export
    all_t = db.get_transactions()
    csv_str = export_transactions_to_csv(all_t)
    assert "Dosa" in csv_str
    assert "Petrol" in csv_str

    # Create fresh DB to import into
    db2 = Database(":memory:")
    res = import_transactions_from_csv(csv_str, db2, cat)
    assert res["imported"] == 2
    assert res["duplicates"] == 0

    # Test duplicate import rejection
    res2 = import_transactions_from_csv(csv_str, db2, cat)
    assert res2["imported"] == 0
    assert res2["duplicates"] == 2


def test_insights_generation(env):
    db, cat, bm = env

    transactions = [
        Transaction(description="Biryani", amount=1200.0, category="Food", transaction_type="expense", transaction_date="2026-10-01"),
        Transaction(description="Biryani", amount=1250.0, category="Food", transaction_type="expense", transaction_date="2026-10-15"),
        Transaction(description="Biryani", amount=1180.0, category="Food", transaction_type="expense", transaction_date="2026-10-25"),
        Transaction(description="Salary", amount=50000.0, category="Salary", transaction_type="income", transaction_date="2026-10-01"),
    ]
    db.insert_transactions_batch(transactions)

    fa = FinancialAnalytics(transactions)
    ig = FinancialInsightsGenerator(fa, bm)
    insights = ig.generate_all_insights(current_month=10, current_year=2026)

    assert len(insights) > 0
    # Food is highest spending category
    assert any("Food is Top Spending Category" in i["title"] for i in insights)
    # Recurring biryani detected
    assert any("Recurring Expense Detected" in i["title"] for i in insights)


def test_markdown_report_generation(env):
    db, cat, bm = env
    transactions = [
        Transaction(description="Dinner", amount=1000.0, category="Food", transaction_type="expense", transaction_date="2026-10-01"),
    ]
    fa = FinancialAnalytics(transactions)
    metrics = fa.get_summary_metrics()
    cat_df = fa.get_category_breakdown()
    ig = FinancialInsightsGenerator(fa, bm)
    insights = ig.generate_all_insights(10, 2026)

    md = generate_markdown_report(metrics, cat_df, insights, "October 2026")
    assert "# 📊 Financial Executive Report" in md
    assert "Dinner" in md or "Food" in md
