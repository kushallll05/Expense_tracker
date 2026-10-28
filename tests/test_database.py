"""
Unit tests for SQLite Database layer.
"""
import pytest
from src.database import Database
from src.models import Transaction, Budget, LearnedMapping


@pytest.fixture
def db():
    return Database(":memory:")


def test_insert_and_get_transaction(db):
    t = Transaction(
        description="Biryani feast",
        amount=450.0,
        category="Food",
        transaction_type="expense",
        transaction_date="2026-10-28",
        payment_method="UPI",
        confidence=0.95
    )
    tid = db.insert_transaction(t)
    assert tid is not None
    assert tid > 0

    fetched = db.get_transaction(tid)
    assert fetched is not None
    assert fetched.description == "Biryani feast"
    assert fetched.amount == 450.0
    assert fetched.category == "Food"


def test_update_and_delete_transaction(db):
    t = Transaction(
        description="Movie tickets",
        amount=300.0,
        category="Entertainment"
    )
    tid = db.insert_transaction(t)

    # Update category and amount
    success = db.update_transaction(tid, {"category": "Other", "amount": 350.0})
    assert success is True

    updated = db.get_transaction(tid)
    assert updated.category == "Other"
    assert updated.amount == 350.0

    # Delete
    deleted = db.delete_transaction(tid)
    assert deleted is True
    assert db.get_transaction(tid) is None


def test_batch_insert_and_filtering(db):
    transactions = [
        Transaction(description="Petrol", amount=500.0, category="Transport", transaction_date="2026-10-01"),
        Transaction(description="Groceries", amount=1200.0, category="Groceries", transaction_date="2026-10-05"),
        Transaction(description="Salary", amount=50000.0, category="Salary", transaction_type="income", transaction_date="2026-10-01"),
    ]
    ids = db.insert_transactions_batch(transactions)
    assert len(ids) == 3

    # Query with category filter
    transport_items = db.get_transactions(category="Transport")
    assert len(transport_items) == 1
    assert transport_items[0].description == "Petrol"

    # Query with transaction_type filter
    income_items = db.get_transactions(transaction_type="income")
    assert len(income_items) == 1
    assert income_items[0].category == "Salary"

    # Search filter
    search_items = db.get_transactions(search="groc")
    assert len(search_items) == 1
    assert search_items[0].description == "Groceries"


def test_budgets_crud(db):
    b = Budget(category="Food", monthly_limit=5000.0, month=10, year=2026)
    db.set_budget(b)

    budgets = db.get_budgets(month=10, year=2026)
    assert len(budgets) == 1
    assert budgets[0].category == "Food"
    assert budgets[0].monthly_limit == 5000.0

    # Update budget limit via upsert
    b_updated = Budget(category="Food", monthly_limit=6000.0, month=10, year=2026)
    db.set_budget(b_updated)
    budgets2 = db.get_budgets(month=10, year=2026)
    assert len(budgets2) == 1
    assert budgets2[0].monthly_limit == 6000.0


def test_learned_mappings_crud(db):
    db.save_learned_mapping("chai point", "Food", merchant="Chai Point")
    mapping = db.get_learned_mapping("chai point")
    assert mapping is not None
    assert mapping.category == "Food"
    assert mapping.merchant == "Chai Point"

    all_maps = db.get_all_learned_mappings()
    assert len(all_maps) == 1

    db.delete_learned_mapping(mapping.id)
    assert db.get_learned_mapping("chai point") is None
