"""
AI & Rule-Based Financial Insights Generator.
Derives deterministic, statistically grounded insights directly from recorded transactions.
Strictly separates observed facts from forecasts. Zero hallucinated figures.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import calendar
from src.analytics import FinancialAnalytics
from src.budget_manager import BudgetManager
from src.config import CURRENCY_SYMBOL
from src.models import Transaction


class FinancialInsightsGenerator:
    def __init__(self, analytics: FinancialAnalytics, budget_manager: Optional[BudgetManager] = None):
        self.analytics = analytics
        self.budget_manager = budget_manager

    def generate_all_insights(self, current_month: Optional[int] = None, current_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Synthesizes financial insights across spending dominance, MoM changes,
        budget pacing, recurring charges, and anomalies.
        """
        insights = []

        now = date.today()
        month = current_month or now.month
        year = current_year or now.year

        # 1. Category Dominance Fact
        top_cat, top_amt, top_pct = self.analytics.get_highest_spending_category()
        if top_cat and top_amt > 0:
            insights.append({
                "type": "FACT",
                "tag": "Observed Fact",
                "title": f"{top_cat} is Top Spending Category",
                "message": f"{top_cat} accounts for {top_pct:.1f}% of your total spending ({CURRENCY_SYMBOL}{top_amt:,.2f}).",
                "icon": "📊",
                "severity": "info" if top_pct < 40 else "warning",
            })

        # 2. Month-over-Month Comparison Fact
        mom = self.analytics.get_mom_comparison()
        if mom.get("has_comparison"):
            pct = mom["expense_change_pct"]
            diff = mom["expense_diff"]
            direction = "increased" if diff > 0 else "decreased"
            icon = "📈" if diff > 0 else "📉"
            severity = "warning" if diff > 0 and abs(pct) > 15 else "success"

            insights.append({
                "type": "FACT",
                "tag": "Observed Fact",
                "title": f"Monthly Spending {direction.capitalize()} by {abs(pct):.1f}%",
                "message": f"Your spending {direction} by {abs(pct):.1f}% ({CURRENCY_SYMBOL}{abs(diff):,.2f}) compared with last month ({mom['previous_month']}).",
                "icon": icon,
                "severity": severity,
            })

        # 3. Budget Pacing Forecast
        if self.budget_manager:
            b_status = self.budget_manager.get_budget_status(month=month, year=year)
            limit = b_status["total_budget_limit"]
            spent = b_status["total_actual_spent"]
            if limit > 0:
                # Calculate pacing based on current day of the month
                days_in_month = calendar.monthrange(year, month)[1]
                current_day = now.day if (now.month == month and now.year == year) else days_in_month
                daily_burn_rate = spent / current_day if current_day > 0 else 0.0
                projected_total = daily_burn_rate * days_in_month

                if projected_total > limit:
                    insights.append({
                        "type": "FORECAST",
                        "tag": "Forecast / Estimate",
                        "title": "Budget Pace Warning",
                        "message": (
                            f"At your current average daily burn rate of {CURRENCY_SYMBOL}{daily_burn_rate:,.2f}/day, "
                            f"your projected monthly spend is {CURRENCY_SYMBOL}{projected_total:,.2f}, "
                            f"which will exceed your total budget of {CURRENCY_SYMBOL}{limit:,.2f}."
                        ),
                        "icon": "⚠️",
                        "severity": "danger",
                    })
                else:
                    insights.append({
                        "type": "FORECAST",
                        "tag": "Forecast / Estimate",
                        "title": "Budget on Track",
                        "message": (
                            f"You are pacing well within your budget limit of {CURRENCY_SYMBOL}{limit:,.2f}. "
                            f"Estimated month-end total is {CURRENCY_SYMBOL}{projected_total:,.2f}."
                        ),
                        "icon": "✅",
                        "severity": "success",
                    })

        # 4. Recurring Expenses Detected
        recurring = self.analytics.identify_recurring_expenses()
        if recurring:
            top_rec = recurring[0]
            insights.append({
                "type": "FACT",
                "tag": "Observed Fact",
                "title": "Recurring Expense Detected",
                "message": f"'{top_rec['description']}' was recorded {top_rec['occurrences']} times averaging {CURRENCY_SYMBOL}{top_rec['average_amount']:,.2f} per transaction.",
                "icon": "🔄",
                "severity": "info",
            })

        # 5. Outliers / Unusual Spending Flagged
        anomalies = self.analytics.detect_unusual_spending()
        if anomalies:
            top_anomaly = anomalies[0]
            insights.append({
                "type": "ALERT",
                "tag": "Spending Anomaly",
                "title": f"Unusual Single Expense: {top_anomaly['description']}",
                "message": f"{top_anomaly['reason']} on {top_anomaly['date']}.",
                "icon": "🚨",
                "severity": "warning",
            })

        # 6. Savings Rate Assessment
        metrics = self.analytics.get_summary_metrics()
        savings_rate = metrics.get("savings_rate", 0.0)
        if metrics["total_income"] > 0:
            if savings_rate >= 30.0:
                insights.append({
                    "type": "FACT",
                    "tag": "Observed Fact",
                    "title": "Strong Savings Rate",
                    "message": f"You are saving {savings_rate:.1f}% of your income this period ({CURRENCY_SYMBOL}{metrics['net_savings']:,.2f} net saved).",
                    "icon": "💎",
                    "severity": "success",
                })
            elif savings_rate < 10.0:
                insights.append({
                    "type": "ALERT",
                    "tag": "Observed Fact",
                    "title": "Low Savings Cushion",
                    "message": f"Your current savings rate is {savings_rate:.1f}%. Consider reviewing non-essential discretionary spending.",
                    "icon": "💡",
                    "severity": "warning",
                })

        return insights
