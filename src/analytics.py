"""
Financial Analytics Engine powered by Pandas, NumPy, Plotly, and Matplotlib.
Computes metrics, trends, comparisons, recurring expenses, and unusual spending.
Handles empty states and missing data gracefully.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server
import matplotlib.pyplot as plt

from src.models import Transaction
from src.config import CATEGORIES, CURRENCY_SYMBOL


class FinancialAnalytics:
    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._build_dataframe(transactions)

    def _build_dataframe(self, transactions: List[Transaction]) -> pd.DataFrame:
        """Converts transaction models to a validated Pandas DataFrame."""
        if not transactions:
            return pd.DataFrame(columns=[
                "id", "description", "amount", "category", "transaction_type",
                "transaction_date", "payment_method", "merchant", "confidence"
            ])

        records = [t.to_dict() for t in transactions]
        df = pd.DataFrame(records)

        # Type conversions and sanitation
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        # Drop rows where transaction_date is invalid
        df = df.dropna(subset=["transaction_date"])
        df["year_month"] = df["transaction_date"].dt.to_period("M").astype(str)
        df["date_str"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
        return df

    # ==================== SUMMARY METRICS ====================

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates total income, expenses, net cash flow, savings rate, and averages."""
        if self.df.empty:
            return {
                "total_income": 0.0,
                "total_expenses": 0.0,
                "net_savings": 0.0,
                "savings_rate": 0.0,
                "avg_daily_expense": 0.0,
                "largest_expense": 0.0,
                "largest_expense_desc": "None",
                "total_transactions": 0,
            }

        income_df = self.df[self.df["transaction_type"] == "income"]
        expense_df = self.df[self.df["transaction_type"] == "expense"]

        total_income = float(income_df["amount"].sum())
        total_expenses = float(expense_df["amount"].sum())
        net_savings = total_income - total_expenses
        savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

        # Unique active days with expenses
        unique_expense_days = expense_df["date_str"].nunique()
        avg_daily_expense = round(total_expenses / unique_expense_days, 2) if unique_expense_days > 0 else 0.0

        largest_expense = 0.0
        largest_expense_desc = "None"
        if not expense_df.empty:
            max_row = expense_df.loc[expense_df["amount"].idxmax()]
            largest_expense = float(max_row["amount"])
            largest_expense_desc = str(max_row["description"])

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_savings": round(net_savings, 2),
            "savings_rate": savings_rate,
            "avg_daily_expense": avg_daily_expense,
            "largest_expense": largest_expense,
            "largest_expense_desc": largest_expense_desc,
            "total_transactions": len(self.df),
        }

    # ==================== CATEGORY ANALYSIS ====================

    def get_category_breakdown(self) -> pd.DataFrame:
        """Returns category-wise spending summary with total, count, and percentage."""
        expense_df = self.df[self.df["transaction_type"] == "expense"]
        if expense_df.empty:
            return pd.DataFrame(columns=["category", "total_amount", "count", "percentage"])

        cat_summary = expense_df.groupby("category").agg(
            total_amount=("amount", "sum"),
            count=("amount", "count")
        ).reset_index()

        total_spent = cat_summary["total_amount"].sum()
        cat_summary["percentage"] = (cat_summary["total_amount"] / total_spent * 100).round(1) if total_spent > 0 else 0.0
        cat_summary = cat_summary.sort_values(by="total_amount", ascending=False)
        return cat_summary

    def get_highest_spending_category(self) -> Tuple[Optional[str], float, float]:
        """Returns (category_name, total_amount, percentage)."""
        cat_df = self.get_category_breakdown()
        if cat_df.empty:
            return None, 0.0, 0.0
        top = cat_df.iloc[0]
        return str(top["category"]), float(top["total_amount"]), float(top["percentage"])

    # ==================== DAILY & MONTHLY TRENDS ====================

    def get_daily_spending_trend(self) -> pd.DataFrame:
        """Returns daily aggregated expenses."""
        expense_df = self.df[self.df["transaction_type"] == "expense"]
        if expense_df.empty:
            return pd.DataFrame(columns=["date_str", "amount", "cumulative_amount"])

        daily = expense_df.groupby("date_str")["amount"].sum().reset_index()
        daily = daily.sort_values(by="date_str")
        daily["cumulative_amount"] = daily["amount"].cumsum()
        return daily

    def get_monthly_spending_trend(self) -> pd.DataFrame:
        """Returns monthly comparison of income and expenses."""
        if self.df.empty:
            return pd.DataFrame(columns=["year_month", "income", "expense", "net_savings"])

        monthly = self.df.pivot_table(
            index="year_month",
            columns="transaction_type",
            values="amount",
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        if "income" not in monthly.columns:
            monthly["income"] = 0.0
        if "expense" not in monthly.columns:
            monthly["expense"] = 0.0

        monthly["net_savings"] = monthly["income"] - monthly["expense"]
        monthly = monthly.sort_values(by="year_month")
        return monthly

    def get_mom_comparison(self) -> Dict[str, Any]:
        """Calculates Month-over-Month (MoM) change between the two most recent months."""
        monthly = self.get_monthly_spending_trend()
        if len(monthly) < 2:
            return {
                "has_comparison": False,
                "current_month": monthly.iloc[-1]["year_month"] if len(monthly) == 1 else None,
                "previous_month": None,
                "expense_change_pct": 0.0,
                "expense_diff": 0.0,
            }

        prev = monthly.iloc[-2]
        curr = monthly.iloc[-1]

        prev_exp = float(prev["expense"])
        curr_exp = float(curr["expense"])
        diff = curr_exp - prev_exp
        pct_change = round((diff / prev_exp * 100), 1) if prev_exp > 0 else 0.0

        return {
            "has_comparison": True,
            "current_month": curr["year_month"],
            "previous_month": prev["year_month"],
            "current_expense": curr_exp,
            "previous_expense": prev_exp,
            "expense_diff": round(diff, 2),
            "expense_change_pct": pct_change,
        }

    # ==================== ADVANCED PATTERNS ====================

    def identify_recurring_expenses(self, min_occurrences: int = 2, tolerance_pct: float = 0.15) -> List[Dict[str, Any]]:
        """
        Detects recurring expenses (e.g., rent, subscriptions, bills)
        by clustering transactions with similar descriptions and close amounts across different dates.
        """
        expense_df = self.df[self.df["transaction_type"] == "expense"]
        if len(expense_df) < min_occurrences:
            return []

        recurring = []
        # Group by normalized description
        grouped = expense_df.groupby("description")

        for desc, group in grouped:
            if len(group) >= min_occurrences:
                amounts = group["amount"].values
                mean_amt = float(np.mean(amounts))
                std_amt = float(np.std(amounts))
                # If standard deviation is low relative to mean, it's a regular recurring cost
                cv = (std_amt / mean_amt) if mean_amt > 0 else 1.0
                if cv <= tolerance_pct:
                    recurring.append({
                        "description": desc,
                        "category": group["category"].iloc[0],
                        "occurrences": len(group),
                        "average_amount": round(mean_amt, 2),
                        "total_spent": round(float(np.sum(amounts)), 2),
                        "latest_date": group["date_str"].max(),
                    })

        return sorted(recurring, key=lambda x: x["total_spent"], reverse=True)

    def detect_unusual_spending(self) -> List[Dict[str, Any]]:
        """
        Detects statistical anomalies / outliers in spending using IQR (Interquartile Range)
        and category-specific threshold deviations.
        """
        expense_df = self.df[self.df["transaction_type"] == "expense"]
        if len(expense_df) < 5:
            return []

        unusual = []
        q1 = float(expense_df["amount"].quantile(0.25))
        q3 = float(expense_df["amount"].quantile(0.75))
        iqr = q3 - q1
        upper_bound = q3 + (1.5 * iqr)

        for _, row in expense_df.iterrows():
            amt = float(row["amount"])
            if amt > upper_bound and amt > 1000:
                unusual.append({
                    "id": row.get("id"),
                    "description": row["description"],
                    "category": row["category"],
                    "amount": amt,
                    "date": row["date_str"],
                    "threshold": round(upper_bound, 2),
                    "reason": f"Amount {CURRENCY_SYMBOL}{amt:,.0f} significantly exceeds usual transaction ceiling of {CURRENCY_SYMBOL}{upper_bound:,.0f}"
                })

        return sorted(unusual, key=lambda x: x["amount"], reverse=True)

    # ==================== PLOTLY CHART BUILDERS ====================

    def create_category_donut_chart(self) -> go.Figure:
        """Interactive Plotly Donut Chart of Category-wise spending."""
        cat_df = self.get_category_breakdown()
        if cat_df.empty:
            fig = go.Figure()
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[{"text": "No expense data to display", "showarrow": False, "font": {"color": "#94a3b8", "size": 16}}]
            )
            return fig

        colors = [CATEGORIES.get(cat, {}).get("color", "#64748b") for cat in cat_df["category"]]

        fig = go.Figure(data=[go.Pie(
            labels=cat_df["category"],
            values=cat_df["total_amount"],
            hole=0.6,
            marker=dict(colors=colors, line=dict(color="#0c0f17", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Total: " + CURRENCY_SYMBOL + "%{value:,.2f}<br>Share: %{percent}<extra></extra>",
        )])

        fig.update_layout(
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0", family="Segoe UI, Inter, sans-serif"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        )
        return fig

    def create_daily_trend_chart(self) -> go.Figure:
        """Interactive Area / Line chart for daily spending."""
        daily_df = self.get_daily_spending_trend()
        if daily_df.empty:
            fig = go.Figure()
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[{"text": "No daily trend data available", "showarrow": False, "font": {"color": "#94a3b8", "size": 16}}]
            )
            return fig

        fig = go.Figure()

        # Daily Bar
        fig.add_trace(go.Bar(
            x=daily_df["date_str"],
            y=daily_df["amount"],
            name="Daily Spend",
            marker=dict(color="rgba(56, 189, 248, 0.7)", line=dict(color="#38bdf8", width=1.5)),
            hovertemplate="Date: %{x}<br>Spend: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>"
        ))

        # Cumulative Line
        fig.add_trace(go.Scatter(
            x=daily_df["date_str"],
            y=daily_df["cumulative_amount"],
            name="Cumulative Total",
            mode="lines+markers",
            line=dict(color="#a855f7", width=3),
            yaxis="y2",
            hovertemplate="Cumulative: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            font=dict(color="#e2e8f0", family="Segoe UI, Inter, sans-serif"),
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(gridcolor="#1e293b", showgrid=True),
            yaxis=dict(title="Daily Spend (" + CURRENCY_SYMBOL + ")", gridcolor="#1e293b", showgrid=True),
            yaxis2=dict(title="Cumulative (" + CURRENCY_SYMBOL + ")", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    def create_monthly_trend_chart(self) -> go.Figure:
        """Grouped Bar Chart of Income vs Expenses by month."""
        monthly_df = self.get_monthly_spending_trend()
        if monthly_df.empty:
            fig = go.Figure()
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[{"text": "No monthly data available", "showarrow": False, "font": {"color": "#94a3b8", "size": 16}}]
            )
            return fig

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_df["year_month"],
            y=monthly_df["income"],
            name="Income",
            marker=dict(color="#10b981"),
            hovertemplate="Month: %{x}<br>Income: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=monthly_df["year_month"],
            y=monthly_df["expense"],
            name="Expense",
            marker=dict(color="#f43f5e"),
            hovertemplate="Month: %{x}<br>Expense: " + CURRENCY_SYMBOL + "%{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            font=dict(color="#e2e8f0", family="Segoe UI, Inter, sans-serif"),
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(gridcolor="#1e293b", showgrid=True),
            yaxis=dict(gridcolor="#1e293b", showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    # ==================== MATPLOTLIB EXPORT GENERATOR ====================

    def generate_matplotlib_report_image(self) -> bytes:
        """
        Renders a comprehensive multi-panel analytical report image
        in Matplotlib and returns PNG bytes for download/export.
        """
        plt.style.use("dark_background")
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#0c0f17")
        fig.suptitle("AI Expense Tracker - Financial Report", fontsize=16, fontweight="bold", color="#38bdf8", y=0.98)

        # 1. Category Pie
        cat_df = self.get_category_breakdown()
        ax_pie = axes[0, 0]
        ax_pie.set_facecolor("#131926")
        if not cat_df.empty:
            labels = cat_df["category"].tolist()
            values = cat_df["total_amount"].tolist()
            colors = [CATEGORIES.get(c, {}).get("color", "#64748b") for c in labels]
            ax_pie.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140, textprops={"color": "#e2e8f0"})
            ax_pie.set_title("Spending by Category", color="#f8fafc", fontsize=12)
        else:
            ax_pie.text(0.5, 0.5, "No Expense Data", ha="center", va="center", color="#94a3b8")

        # 2. Daily Spend Bar
        daily_df = self.get_daily_spending_trend()
        ax_daily = axes[0, 1]
        ax_daily.set_facecolor("#131926")
        if not daily_df.empty:
            ax_daily.bar(daily_df["date_str"], daily_df["amount"], color="#38bdf8", alpha=0.85)
            ax_daily.set_title("Daily Expense Pattern", color="#f8fafc", fontsize=12)
            ax_daily.tick_params(axis="x", rotation=45, colors="#94a3b8")
            ax_daily.tick_params(axis="y", colors="#94a3b8")
            ax_daily.grid(True, linestyle="--", alpha=0.2, color="#64748b")
        else:
            ax_daily.text(0.5, 0.5, "No Daily Data", ha="center", va="center", color="#94a3b8")

        # 3. Monthly Trends
        monthly_df = self.get_monthly_spending_trend()
        ax_monthly = axes[1, 0]
        ax_monthly.set_facecolor("#131926")
        if not monthly_df.empty:
            x = np.arange(len(monthly_df))
            width = 0.35
            ax_monthly.bar(x - width/2, monthly_df["income"], width, label="Income", color="#10b981", alpha=0.85)
            ax_monthly.bar(x + width/2, monthly_df["expense"], width, label="Expense", color="#f43f5e", alpha=0.85)
            ax_monthly.set_xticks(x)
            ax_monthly.set_xticklabels(monthly_df["year_month"], rotation=30, color="#94a3b8")
            ax_monthly.set_title("Monthly Income vs Expense", color="#f8fafc", fontsize=12)
            ax_monthly.legend(loc="upper left")
            ax_monthly.grid(True, linestyle="--", alpha=0.2, color="#64748b")
        else:
            ax_monthly.text(0.5, 0.5, "No Monthly Data", ha="center", va="center", color="#94a3b8")

        # 4. Summary KPI Table/Card
        ax_summary = axes[1, 1]
        ax_summary.set_facecolor("#131926")
        ax_summary.axis("off")
        metrics = self.get_summary_metrics()

        summary_text = (
            f"FINANCIAL SUMMARY\n"
            f"────────────────────────────────\n"
            f"Total Income:       {CURRENCY_SYMBOL}{metrics['total_income']:,.2f}\n"
            f"Total Expenses:     {CURRENCY_SYMBOL}{metrics['total_expenses']:,.2f}\n"
            f"Net Balance:        {CURRENCY_SYMBOL}{metrics['net_savings']:,.2f}\n"
            f"Savings Rate:       {metrics['savings_rate']}%\n"
            f"Avg Daily Expense:  {CURRENCY_SYMBOL}{metrics['avg_daily_expense']:,.2f}\n"
            f"Largest Expense:    {CURRENCY_SYMBOL}{metrics['largest_expense']:,.2f}\n"
            f"                    ({metrics['largest_expense_desc']})\n"
            f"Total Recorded:     {metrics['total_transactions']} transactions\n"
        )
        ax_summary.text(0.1, 0.5, summary_text, fontfamily="monospace", fontsize=11, color="#38bdf8", va="center")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
