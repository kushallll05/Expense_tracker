"""
Unit tests for Amount and Description Parser.
"""
import pytest
from src.amount_parser import parse_natural_language_expenses, parse_single_expense


def test_basic_amount_and_description():
    res = parse_natural_language_expenses("Petrol 500")
    assert len(res) == 1
    assert res[0]["amount"] == 500.0
    assert "Petrol" in res[0]["description"]


def test_k_shorthand():
    res = parse_natural_language_expenses("2k for biryani")
    assert len(res) == 1
    assert res[0]["amount"] == 2000.0
    assert "Biryani" in res[0]["description"]


def test_fractional_k_shorthand():
    res = parse_natural_language_expenses("Shoes for 2.5k")
    assert len(res) == 1
    assert res[0]["amount"] == 2500.0
    assert "Shoes" in res[0]["description"]


def test_lakh_shorthand():
    res = parse_natural_language_expenses("2 lakh for car down payment")
    assert len(res) == 1
    assert res[0]["amount"] == 200000.0
    assert "Car Down Payment" in res[0]["description"]


def test_currency_symbol_and_commas():
    res = parse_natural_language_expenses("Paid ₹2,000 for electricity bill")
    assert len(res) == 1
    assert res[0]["amount"] == 2000.0
    assert "Electricity Bill" in res[0]["description"]


def test_user_examples():
    cases = [
        ("Bought Nike shoes for 3500", 3500.0, "Nike Shoes"),
        ("Paid electricity bill 1200", 1200.0, "Electricity Bill"),
        ("Dosa and coffee 150", 150.0, "Dosa And Coffee"),
        ("Bought Python course for 999", 999.0, "Python Course"),
        ("Movie ticket 300", 300.0, "Movie Ticket"),
        ("Doctor consultation 500", 500.0, "Doctor Consultation"),
        ("Milk, eggs and vegetables 250", 250.0, "Milk, Eggs And Vegetables"),
        ("Haircut 150", 150.0, "Haircut"),
    ]
    for text, expected_amount, expected_desc in cases:
        parsed = parse_natural_language_expenses(text)
        assert len(parsed) == 1, f"Failed on input: {text}"
        assert parsed[0]["amount"] == expected_amount, f"Amount mismatch on: {text}"
        assert expected_desc.lower() in parsed[0]["description"].lower(), f"Desc mismatch on: {text}"


def test_multi_expense_input():
    text = "500 petrol, 200 coffee, 1200 electricity bill"
    res = parse_natural_language_expenses(text)
    assert len(res) == 3
    assert res[0]["amount"] == 500.0
    assert "Petrol" in res[0]["description"]
    assert res[1]["amount"] == 200.0
    assert "Coffee" in res[1]["description"]
    assert res[2]["amount"] == 1200.0
    assert "Electricity Bill" in res[2]["description"]


def test_multi_expense_with_and():
    text = "2k biryani and 500 petrol"
    res = parse_natural_language_expenses(text)
    assert len(res) == 2
    assert res[0]["amount"] == 2000.0
    assert "Biryani" in res[0]["description"]
    assert res[1]["amount"] == 500.0
    assert "Petrol" in res[1]["description"]


def test_invalid_input_no_amount():
    res = parse_natural_language_expenses("Just a random conversation with no numbers")
    assert len(res) == 0


def test_empty_string():
    res = parse_natural_language_expenses("")
    assert len(res) == 0
