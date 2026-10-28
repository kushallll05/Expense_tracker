"""
Unit tests for BudgetManager.
"""
import pytest
from src.database import Database
from src.budget_manager import BudgetManager
from src.models import Transaction


@pytest.fixture
def budget_system():
    db = Database(":memory:")
    bm = BudgetManager(db)
    return db, bm


def test_budget_threshold_states(budget_system):
    db, bm = budget_system

    # Set budget of 5000 for Food in Oct 2026
    bm.set_category_budget("Food", 5000.0, month=10, year=2026)

    # 1. Under 80% (safe)
    transactions = [
        Transaction(description="Lunch", amount=2000.0, category="Food", transaction_type="expense", transaction_date="2026-10-10")
    ]
    status = bm.get_budget_status(month=10, year=2026, transactions=transactions)
    food_status = status["category_budgets"][0]
    assert food_status["status"] == "safe"
    assert food_status["percentage"] == 40.0
    assert food_status["remaining"] == 3000.0

    # 2. Between 80% and 100% (warning)
    transactions.append(
        Transaction(description="Dinner party", amount=2200.0, category="Food", transaction_type="expense", transaction_date="2026-10-15")
    )
    # Total spent: 4200 (84%)
    status2 = bm.get_budget_status(month=10, year=2026, transactions=transactions)
    food_status2 = status2["category_budgets"][0]
    assert food_status2["status"] == "warning"
    assert food_status2["percentage"] == 84.0

    # 3. Over 100% (exceeded)
    transactions.append(
        Transaction(description="Gourmet treat", amount=1000.0, category="Food", transaction_type="expense", transaction_date="2026-10-20")
    )
    # Total spent: 5200 (104%)
    status3 = bm.get_budget_status(month=10, year=2026, transactions=transactions)
    food_status3 = status3["category_budgets"][0]
    assert food_status3["status"] == "exceeded"
    assert food_status3["percentage"] == 104.0
    assert food_status3["remaining"] == -200.0
