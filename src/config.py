"""
Configuration settings for AI Expense Tracker.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = str(DATA_DIR / "expenses.db")

# Database Path
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

# Ollama Config
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = 5

# Categorization Confidence
HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.45

# Standard Categories with metadata
CATEGORIES = {
    "Food": {
        "icon": "🍔",
        "color": "#f59e0b",
        "description": "Dining out, cafes, snacks, meals, delivery",
        "three_color": 0xf59e0b,
    },
    "Shopping": {
        "icon": "🛍️",
        "color": "#ec4899",
        "description": "Clothing, electronics, gadgets, footwear, retail",
        "three_color": 0xec4899,
    },
    "Transport": {
        "icon": "🚗",
        "color": "#3b82f6",
        "description": "Petrol, diesel, cab, metro, auto, train, flight, parking",
        "three_color": 0x3b82f6,
    },
    "Bills": {
        "icon": "💡",
        "color": "#8b5cf6",
        "description": "Electricity, water, gas, broadband, phone recharge, rent",
        "three_color": 0x8b5cf6,
    },
    "Groceries": {
        "icon": "🛒",
        "color": "#10b981",
        "description": "Supermarket, vegetables, fruits, dairy, provisions",
        "three_color": 0x10b981,
    },
    "Education": {
        "icon": "📚",
        "color": "#06b6d4",
        "description": "Courses, books, tuition, certifications, stationery",
        "three_color": 0x06b6d4,
    },
    "Entertainment": {
        "icon": "🎬",
        "color": "#f43f5e",
        "description": "Movies, concerts, OTT streaming, games, outings",
        "three_color": 0xf43f5e,
    },
    "Health": {
        "icon": "🩺",
        "color": "#14b8a6",
        "description": "Doctor fees, pharmacy, medicine, lab tests, gym, therapy",
        "three_color": 0x14b8a6,
    },
    "Personal Care": {
        "icon": "💇",
        "color": "#a855f7",
        "description": "Salon, haircut, cosmetics, spa, grooming",
        "three_color": 0xa855f7,
    },
    "Investment": {
        "icon": "📈",
        "color": "#22c55e",
        "description": "Mutual funds, stocks, crypto, gold, deposits",
        "three_color": 0x22c55e,
    },
    "Salary": {
        "icon": "💰",
        "color": "#38bdf8",
        "description": "Monthly salary, bonus, freelance earnings, client pay",
        "three_color": 0x38bdf8,
    },
    "Other": {
        "icon": "📦",
        "color": "#64748b",
        "description": "Miscellaneous or unclassified transactions",
        "three_color": 0x64748b,
    },
}

EXPENSE_CATEGORIES = [k for k in CATEGORIES.keys() if k != "Salary"]
ALL_CATEGORIES = list(CATEGORIES.keys())
DEFAULT_CURRENCY = "INR"
CURRENCY_SYMBOL = "₹"
