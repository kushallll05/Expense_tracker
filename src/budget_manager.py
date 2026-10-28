"""
Budget Manager for tracking category and overall monthly spending thresholds,
progress percentages, and early warning alerts.
"""
from typing import List, Dict, Any, Optional
from datetime import date
from src.database import Database
from src.models import Budget, Transaction


class BudgetManager:
    def __init__(self, db: Database):
        self.db = db

    def set_category_budget(self, category: str, monthly_limit: float, month: int, year: int) -> int:
        """Sets or updates a budget for a category."""
        budget = Budget(category=category, monthly_limit=monthly_limit, month=month, year=year)
        return self.db.set_budget(budget)

    def delete_budget(self, budget_id: int) -> bool:
        """Deletes a budget limit."""
        return self.db.delete_budget(budget_id)

    def get_budget_status(self, month: int, year: int, transactions: Optional[List[Transaction]] = None) -> Dict[str, Any]:
        """
        Calculates spending against budgets for a specific month and year.
        Returns overall budget usage and per-category progress breakdown.
        """
        # Fetch configured budgets
        budgets = self.db.get_budgets(month=month, year=year)
        budget_map = {b.category: b for b in budgets}

        # Filter transactions for this month/year if not provided
        if transactions is None:
            # Query transactions for this month
            start_date = f"{year:04d}-{month:02d}-01"
            # End date (last day of month approx or 31)
            end_date = f"{year:04d}-{month:02d}-31"
            transactions = self.db.get_transactions(start_date=start_date, end_date=end_date)

        # Aggregate actual spending by category
        cat_spending: Dict[str, float] = {}
        for t in transactions:
            if t.transaction_type == "expense":
                try:
                    t_date = date.fromisoformat(t.transaction_date)
                    if t_date.month == month and t_date.year == year:
                        cat_spending[t.category] = cat_spending.get(t.category, 0.0) + float(t.amount)
                except (ValueError, TypeError):
                    continue

        category_statuses = []
        total_budget_limit = 0.0
        total_actual_spent = 0.0

        # Process categories with configured budgets
        for b in budgets:
            actual = cat_spending.get(b.category, 0.0)
            limit = b.monthly_limit
            remaining = limit - actual
            pct = round((actual / limit * 100), 1) if limit > 0 else 0.0

            if pct > 100.0:
                status = "exceeded"
                status_label = "Exceeded Budget"
                color = "#f43f5e"
            elif pct >= 80.0:
                status = "warning"
                status_label = "Approaching Limit"
                color = "#f59e0b"
            else:
                status = "safe"
                status_label = "Within Budget"
                color = "#10b981"

            total_budget_limit += limit
            total_actual_spent += actual

            category_statuses.append({
                "budget_id": b.id,
                "category": b.category,
                "limit": limit,
                "spent": round(actual, 2),
                "remaining": round(remaining, 2),
                "percentage": pct,
                "status": status,
                "status_label": status_label,
                "color": color,
            })

        # Overall budget usage
        overall_pct = round((total_actual_spent / total_budget_limit * 100), 1) if total_budget_limit > 0 else 0.0
        overall_remaining = total_budget_limit - total_actual_spent

        if overall_pct > 100.0:
            overall_status = "exceeded"
        elif overall_pct >= 80.0:
            overall_status = "warning"
        else:
            overall_status = "safe"

        return {
            "month": month,
            "year": year,
            "total_budget_limit": round(total_budget_limit, 2),
            "total_actual_spent": round(total_actual_spent, 2),
            "total_remaining": round(overall_remaining, 2),
            "overall_percentage": overall_pct,
            "overall_status": overall_status,
            "category_budgets": category_statuses,
            "warnings_count": sum(1 for c in category_statuses if c["status"] in ("warning", "exceeded")),
        }
