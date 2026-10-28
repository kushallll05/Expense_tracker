"""
Unit tests for TransactionService.
"""
import pytest
from src.database import Database
from src.transaction_service import TransactionService
from src.models import Transaction


@pytest.fixture
def service():
    db = Database(":memory:")
    return TransactionService(db=db, use_ollama=False)


def test_parse_and_save_flow(service):
    # Parse natural language input
    parsed = service.parse_and_categorize_input("2k for biryani", transaction_date="2026-10-28")
    assert len(parsed) == 1
    assert parsed[0].amount == 2000.0
    assert parsed[0].category == "Food"

    # Save to database
    ids = service.save_parsed_expenses(parsed, payment_method="UPI")
    assert len(ids) == 1
    tid = ids[0]

    # Fetch from database
    t = service.get_transaction(tid)
    assert t is not None
    assert t.amount == 2000.0
    assert t.category == "Food"
    assert "Biryani" in t.description


def test_update_learns_category(service):
    # Insert an ambiguous transaction
    t = Transaction(
        description="Mystic Gadget X",
        amount=1500.0,
        category="Other",
        transaction_date="2026-10-28"
    )
    tid = service.add_transaction(t)

    # User manually corrects category to "Shopping"
    service.update_transaction(tid, {"category": "Shopping"}, learn_correction=True)

    # Check that learned mapping is stored
    mappings = service.get_learned_mappings()
    assert any(m.normalized_description == "mystic gadget x" and m.category == "Shopping" for m in mappings)

    # Next time user enters "Mystic Gadget X 1800", it should auto-categorize to Shopping!
    new_parsed = service.parse_and_categorize_input("Mystic Gadget X 1800")
    assert len(new_parsed) == 1
    assert new_parsed[0].amount == 1800.0
    assert new_parsed[0].category == "Shopping"
    assert new_parsed[0].confidence == 1.0


def test_multi_expense_service_flow(service):
    input_text = "500 petrol, 200 coffee, 1200 electricity bill"
    parsed = service.parse_and_categorize_input(input_text)
    assert len(parsed) == 3

    ids = service.save_parsed_expenses(parsed)
    assert len(ids) == 3

    all_trans = service.get_transactions()
    assert len(all_trans) == 3
