"""
Unit tests for Expense Categorizer.
"""
import pytest
from src.categorizer import Categorizer
from src.database import Database
from src.amount_parser import parse_natural_language_expenses


@pytest.fixture
def test_db():
    return Database(":memory:")


@pytest.fixture
def categorizer(test_db):
    return Categorizer(db=test_db, use_ollama=False)


def test_food_categorization(categorizer):
    res = categorizer.categorize("Biryani", 2000.0)
    assert res.category == "Food"
    assert res.confidence >= 0.75
    assert not res.is_ambiguous


def test_transport_categorization(categorizer):
    res = categorizer.categorize("Petrol", 500.0)
    assert res.category == "Transport"
    assert res.confidence >= 0.75
    assert not res.is_ambiguous


def test_shopping_categorization(categorizer):
    res = categorizer.categorize("Nike shoes", 3500.0)
    assert res.category == "Shopping"
    assert res.confidence >= 0.75
    assert not res.is_ambiguous


def test_bills_categorization(categorizer):
    res = categorizer.categorize("Electricity bill", 1200.0)
    assert res.category == "Bills"
    assert res.confidence >= 0.75


def test_groceries_categorization(categorizer):
    res = categorizer.categorize("Milk, eggs and vegetables", 250.0)
    assert res.category == "Groceries"
    assert res.confidence >= 0.75


def test_education_categorization(categorizer):
    res = categorizer.categorize("Python course", 999.0)
    assert res.category == "Education"
    assert res.confidence >= 0.75


def test_entertainment_categorization(categorizer):
    res = categorizer.categorize("Movie ticket", 300.0)
    assert res.category == "Entertainment"
    assert res.confidence >= 0.75


def test_health_categorization(categorizer):
    res = categorizer.categorize("Doctor consultation", 500.0)
    assert res.category == "Health"
    assert res.confidence >= 0.75


def test_personal_care_categorization(categorizer):
    res = categorizer.categorize("Haircut", 150.0)
    assert res.category == "Personal Care"
    assert res.confidence >= 0.75


def test_ambiguous_and_unknown_description(categorizer):
    res = categorizer.categorize("Mysterious vortex widget", 450.0)
    assert res.category == "Other"
    assert res.confidence < 0.75
    assert res.is_ambiguous is True


def test_learned_user_correction_precedence(test_db, categorizer):
    # Suppose "Apple" is typically fruit/grocery or tech shopping, but user explicitly corrects it to Education
    test_db.save_learned_mapping("apple study tool", "Education")

    # Now classify with learned mapping
    res = categorizer.categorize("Apple study tool", 250.0)
    assert res.category == "Education"
    assert res.confidence == 1.0
    assert not res.is_ambiguous
    assert "learned" in res.reasoning.lower()


def test_pipeline_integration(categorizer):
    # Testing amount parsing directly followed by categorizer
    parsed_items = parse_natural_language_expenses("2k for biryani")
    item = parsed_items[0]
    res = categorizer.categorize(item["description"], item["amount"], item["raw_amount_str"], item["source_text"])
    assert res.amount == 2000.0
    assert res.category == "Food"
    assert "Biryani" in res.description
