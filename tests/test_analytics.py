"""
Unit tests for FinancialAnalytics.
"""
import pytest
from src.models import Transaction
from src.analytics import FinancialAnalytics


@pytest.fixture
def sample_transactions():
    return [
        Transaction(description="Biryani", amount=500.0, category="Food", transaction_type="expense", transaction_date="2026-10-01"),
        Transaction(description="Coffee & Dosa", amount=200.0, category="Food", transaction_type="expense", transaction_date="2026-10-02"),
        Transaction(description="Petrol", amount=800.0, category="Transport", transaction_type="expense", transaction_date="2026-10-02"),
        Transaction(description="Electricity Bill", amount=1500.0, category="Bills", transaction_type="expense", transaction_date="2026-10-05"),
        Transaction(description="Salary", amount=50000.0, category="Salary", transaction_type="income", transaction_date="2026-10-01"),
        # September transactions for MoM comparison
        Transaction(description="Past Petrol", amount=600.0, category="Transport", transaction_type="expense", transaction_date="2026-09-15"),
        Transaction(description="Past Salary", amount=50000.0, category="Salary", transaction_type="income", transaction_date="2026-09-01"),
    ]


def test_empty_analytics():
    fa = FinancialAnalytics([])
    metrics = fa.get_summary_metrics()
    assert metrics["total_income"] == 0.0
    assert metrics["total_expenses"] == 0.0
    assert metrics["net_savings"] == 0.0
    assert metrics["savings_rate"] == 0.0

    cat_df = fa.get_category_breakdown()
    assert cat_df.empty


def test_summary_metrics(sample_transactions):
    fa = FinancialAnalytics(sample_transactions)
    metrics = fa.get_summary_metrics()

    # Total income: 50,000 + 50,000 = 100,000
    assert metrics["total_income"] == 100000.0
    # Total expenses: 500 + 200 + 800 + 1500 + 600 = 3600
    assert metrics["total_expenses"] == 3600.0
    assert metrics["net_savings"] == 96400.0
    assert metrics["largest_expense"] == 1500.0
    assert metrics["largest_expense_desc"] == "Electricity Bill"


def test_category_breakdown(sample_transactions):
    fa = FinancialAnalytics(sample_transactions)
    cat_df = fa.get_category_breakdown()
    assert not cat_df.empty

    food_row = cat_df[cat_df["category"] == "Food"].iloc[0]
    assert food_row["total_amount"] == 700.0  # 500 + 200
    assert food_row["count"] == 2


def test_mom_comparison(sample_transactions):
    fa = FinancialAnalytics(sample_transactions)
    mom = fa.get_mom_comparison()
    assert mom["has_comparison"] is True
    assert mom["previous_month"] == "2026-09"
    assert mom["current_month"] == "2026-10"
    assert mom["current_expense"] == 3000.0  # 500 + 200 + 800 + 1500
    assert mom["previous_expense"] == 600.0


def test_matplotlib_report_generation(sample_transactions):
    fa = FinancialAnalytics(sample_transactions)
    png_bytes = fa.generate_matplotlib_report_image()
    assert len(png_bytes) > 1000  # valid image bytes
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic header
