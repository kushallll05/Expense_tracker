"""
Data models for transactions, budgets, mappings, and parsed natural language expenses.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, List, Dict, Any


@dataclass
class Transaction:
    description: str
    amount: float
    category: str
    transaction_type: str = "expense"  # 'expense' or 'income'
    transaction_date: str = field(default_factory=lambda: date.today().isoformat())
    payment_method: str = "UPI"
    merchant: Optional[str] = None
    source_text: Optional[str] = None
    confidence: float = 1.0
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Budget:
    category: str
    monthly_limit: float
    month: int
    year: int
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearnedMapping:
    normalized_description: str
    category: str
    merchant: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedExpense:
    amount: float
    description: str
    category: str
    confidence: float
    transaction_type: str = "expense"
    merchant: Optional[str] = None
    transaction_date: Optional[str] = None
    source_text: Optional[str] = None
    raw_amount_str: Optional[str] = None
    is_ambiguous: bool = False
    reasoning: Optional[str] = None

    def to_transaction(self, payment_method: str = "UPI") -> Transaction:
        return Transaction(
            description=self.description,
            amount=self.amount,
            category=self.category,
            transaction_type=self.transaction_type,
            transaction_date=self.transaction_date or date.today().isoformat(),
            payment_method=payment_method,
            merchant=self.merchant,
            source_text=self.source_text,
            confidence=self.confidence,
        )
