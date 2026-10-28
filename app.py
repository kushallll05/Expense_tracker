"""
AI-Based Expense Tracker with an Interactive 3D Dashboard.
Main Streamlit Application.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import os

from src.config import (
    CATEGORIES,
    ALL_CATEGORIES,
    EXPENSE_CATEGORIES,
    CURRENCY_SYMBOL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from src.database import Database
from src.models import Transaction, Budget, ParsedExpense
from src.transaction_service import TransactionService
from src.analytics import FinancialAnalytics
from src.budget_manager import BudgetManager
from src.insights import FinancialInsightsGenerator
from src.csv_manager import (
    export_transactions_to_csv,
    import_transactions_from_csv,
    generate_markdown_report,
)
from ui.components import (
    render_metric_card,
    render_insight_card,
    render_budget_progress,
)
from ui.three_d_dashboard import render_three_d_dashboard_html

# Page Configuration
st.set_page_config(
    page_title="AI Expense Tracker • 3D Financial OS",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "ui", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Core Services (cached in session state)
if "db" not in st.session_state:
    st.session_state.db = Database()

if "use_ollama" not in st.session_state:
    st.session_state.use_ollama = True

if "service" not in st.session_state:
    st.session_state.service = TransactionService(
        db=st.session_state.db,
        use_ollama=st.session_state.use_ollama
    )

if "active_category_filter" not in st.session_state:
    st.session_state.active_category_filter = "All"

db = st.session_state.db
service = st.session_state.service
budget_mgr = BudgetManager(db)

# ==================== SIDEBAR NAVIGATION ====================
with st.sidebar:
    st.markdown("### 🌌 AI Financial OS")
    st.caption("3D Interactive Expense & Wealth Tracker")
    st.markdown("---")

    nav_selection = st.radio(
        "Navigation",
        [
            "Overview",
            "Transactions",
            "Categories",
            "Budgets",
            "Analytics",
            "AI Insights",
            "Settings & CSV"
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### 📅 Period Selector")
    today = date.today()
    selected_year = st.selectbox("Year", options=[today.year - 1, today.year, today.year + 1], index=1)
    selected_month = st.selectbox(
        "Month",
        options=list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda m: calendar.month_name[m]
    )

    st.markdown("---")
    st.markdown("#### 🤖 AI Engine")
    use_ollama_toggle = st.toggle("Enable Local LLM (Ollama)", value=st.session_state.use_ollama)
    if use_ollama_toggle != st.session_state.use_ollama:
        st.session_state.use_ollama = use_ollama_toggle
        st.session_state.service = TransactionService(db=db, use_ollama=use_ollama_toggle)
        st.rerun()

    if st.session_state.use_ollama:
        st.caption(f"Model: `{OLLAMA_MODEL}` (Local)")
    else:
        st.caption("Mode: Rule-Based Classifier (Offline)")

    st.markdown("---")
    # Quick Sample Data Loader if DB is completely empty
    total_tx_count = db.count_transactions()
    if total_tx_count == 0:
        if st.button("🚀 Load Sample Transactions"):
            sample_data = [
                Transaction("Biryani feast with friends", 2000.0, "Food", "expense", f"{selected_year}-{selected_month:02d}-02", "UPI"),
                Transaction("Bought Nike running shoes", 3500.0, "Shopping", "expense", f"{selected_year}-{selected_month:02d}-04", "Credit Card"),
                Transaction("Petrol fuel refill", 600.0, "Transport", "expense", f"{selected_year}-{selected_month:02d}-06", "UPI"),
                Transaction("Paid electricity bill", 1200.0, "Bills", "expense", f"{selected_year}-{selected_month:02d}-08", "Net Banking"),
                Transaction("Dosa and filter coffee", 150.0, "Food", "expense", f"{selected_year}-{selected_month:02d}-10", "UPI"),
                Transaction("Bought Python data science course", 999.0, "Education", "expense", f"{selected_year}-{selected_month:02d}-12", "Credit Card"),
                Transaction("Weekend movie ticket", 300.0, "Entertainment", "expense", f"{selected_year}-{selected_month:02d}-15", "UPI"),
                Transaction("Doctor consultation fee", 500.0, "Health", "expense", f"{selected_year}-{selected_month:02d}-17", "Cash"),
                Transaction("Milk, eggs and fresh vegetables", 250.0, "Groceries", "expense", f"{selected_year}-{selected_month:02d}-19", "UPI"),
                Transaction("Salon haircut & beard trim", 150.0, "Personal Care", "expense", f"{selected_year}-{selected_month:02d}-21", "UPI"),
                Transaction("Monthly Salary Credit", 75000.0, "Salary", "income", f"{selected_year}-{selected_month:02d}-01", "Net Banking"),
            ]
            db.insert_transactions_batch(sample_data)
            # Also set sample budgets
            budget_mgr.set_category_budget("Food", 4000.0, selected_month, selected_year)
            budget_mgr.set_category_budget("Shopping", 5000.0, selected_month, selected_year)
            budget_mgr.set_category_budget("Transport", 2000.0, selected_month, selected_year)
            budget_mgr.set_category_budget("Bills", 3000.0, selected_month, selected_year)
            st.success("Sample financial dataset loaded!")
            st.rerun()


# ==================== DATA FETCHING FOR SELECTED PERIOD ====================
start_date = f"{selected_year:04d}-{selected_month:02d}-01"
last_day = calendar.monthrange(selected_year, selected_month)[1]
end_date = f"{selected_year:04d}-{selected_month:02d}-{last_day:02d}"

# Fetch period transactions and all-time transactions
period_transactions = service.get_transactions(start_date=start_date, end_date=end_date)
all_transactions = service.get_transactions()

analytics = FinancialAnalytics(period_transactions)
all_analytics = FinancialAnalytics(all_transactions)
metrics = analytics.get_summary_metrics()
insights_gen = FinancialInsightsGenerator(analytics, budget_mgr)


# ==================== PROMINENT NATURAL LANGUAGE EXPENSE INPUT ====================
st.markdown("## ⚡ Fast Expense Entry (Natural Language)")

with st.container():
    st.markdown("""
    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px;">
      Type anything naturally, e.g., <code>2k for biryani</code>, <code>Petrol 600</code>, <code>Bought Nike shoes for 3500</code>, or multi-expense <code>500 petrol, 200 coffee, 1200 electricity bill</code>.
    </div>
    """, unsafe_allow_html=True)

    col_input, col_date, col_pay, col_btn = st.columns([5, 2, 2, 1.5])
    with col_input:
        nl_input = st.text_input(
            "Expense Description",
            placeholder="Enter an expense, e.g. 2k for biryani",
            label_visibility="collapsed",
            key="nl_expense_input"
        )
    with col_date:
        entry_date = st.date_input("Date", value=today, label_visibility="collapsed")
    with col_pay:
        payment_method = st.selectbox(
            "Payment Method",
            options=["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking", "Other"],
            index=0,
            label_visibility="collapsed"
        )
    with col_btn:
        submit_expense = st.button("✨ Add Expense", type="primary", use_container_width=True)

    # Quick example pill chips
    chip_cols = st.columns(6)
    examples = [
        "2k for biryani",
        "Petrol 600",
        "Bought Nike shoes for 3500",
        "Paid electricity bill 1200",
        "Dosa and coffee 150",
        "500 petrol, 200 coffee, 1200 electricity bill"
    ]

    if submit_expense and nl_input:
        parsed_items = service.parse_and_categorize_input(nl_input, transaction_date=entry_date.isoformat())
        if not parsed_items:
            st.error("⚠️ Could not extract an amount from your input. Please include a number, e.g., '2k for biryani' or 'Petrol 500'.")
        else:
            saved_ids = service.save_parsed_expenses(parsed_items, payment_method=payment_method)
            st.success(f"🎉 Successfully recorded {len(saved_ids)} transaction(s)!")
            for item in parsed_items:
                st.info(f"**Saved:** {item.description} • **Amount:** {CURRENCY_SYMBOL}{item.amount:,.2f} • **Category:** {item.category} • **Confidence:** {item.confidence*100:.0f}%")
            st.rerun()

st.markdown("---")


# ==================== PAGE 1: OVERVIEW ====================
if nav_selection == "Overview":
    st.subheader(f"📊 Financial Summary • {calendar.month_name[selected_month]} {selected_year}")

    # Top KPI Summary Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Total Income", f"{CURRENCY_SYMBOL}{metrics['total_income']:,.2f}", "Monthly Inflow", "💰", "+Income", "income")
    with kpi2:
        render_metric_card("Total Expenses", f"{CURRENCY_SYMBOL}{metrics['total_expenses']:,.2f}", f"{metrics['total_transactions']} txns", "💸", "-Spent", "expense")
    with kpi3:
        bal_color = "income" if metrics['net_savings'] >= 0 else "expense"
        render_metric_card("Net Balance", f"{CURRENCY_SYMBOL}{metrics['net_savings']:,.2f}", "Monthly Margin", "⚖️", f"{metrics['savings_rate']}% Saved", bal_color)
    with kpi4:
        top_cat, top_amt, _ = analytics.get_highest_spending_category()
        top_cat_display = f"{top_cat} ({CURRENCY_SYMBOL}{top_amt:,.0f})" if top_cat else "None"
        render_metric_card("Top Category", top_cat or "None", f"{CURRENCY_SYMBOL}{top_amt:,.2f}", "👑", "Highest", "warning")
    with kpi5:
        b_status = budget_mgr.get_budget_status(selected_month, selected_year, period_transactions)
        b_pct = b_status["overall_percentage"]
        b_badge = "income" if b_pct < 80 else ("warning" if b_pct <= 100 else "expense")
        render_metric_card("Budget Usage", f"{b_pct:.0f}%", f"{CURRENCY_SYMBOL}{b_status['total_actual_spent']:,.0f} / {CURRENCY_SYMBOL}{b_status['total_budget_limit']:,.0f}", "🎯", b_status["overall_status"].capitalize(), b_badge)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3D Interactive Visualization
    st.markdown("### 🪐 Interactive 3D Financial Visualization")
    cat_df = analytics.get_category_breakdown()
    cat_records = cat_df.to_dict(orient="records") if not cat_df.empty else []

    three_d_html = render_three_d_dashboard_html(
        category_data=cat_records,
        total_expenses=metrics["total_expenses"],
        height=540
    )
    st.components.v1.html(three_d_html, height=550, scrolling=False)

    # Interactive Category Pills
    st.markdown("#### Filter by Category")
    pill_cols = st.columns(len(EXPENSE_CATEGORIES) + 1)
    with pill_cols[0]:
        if st.button("All Categories", key="filter_all", use_container_width=True):
            st.session_state.active_category_filter = "All"
            st.rerun()

    for i, cat in enumerate(EXPENSE_CATEGORIES):
        with pill_cols[i + 1]:
            meta = CATEGORIES.get(cat, {})
            label = f"{meta.get('icon', '')} {cat}"
            if st.button(label, key=f"filter_pill_{cat}", use_container_width=True):
                st.session_state.active_category_filter = cat
                st.rerun()

    if st.session_state.active_category_filter != "All":
        st.info(f"Filtering recent transactions by: **{st.session_state.active_category_filter}** (Click 'All Categories' to reset)")

    # Charts & Breakdown Row
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("#### 🍩 Category Breakdown")
        donut_fig = analytics.create_category_donut_chart()
        st.plotly_chart(donut_fig, use_container_width=True)

    with c_right:
        st.markdown("#### 📈 Daily Spending Trend")
        trend_fig = analytics.create_daily_trend_chart()
        st.plotly_chart(trend_fig, use_container_width=True)

    # Recent Transactions Feed
    st.markdown("#### 🕒 Recent Transactions")
    filtered_recent = [
        t for t in period_transactions
        if (st.session_state.active_category_filter == "All" or t.category == st.session_state.active_category_filter)
    ][:6]

    if not filtered_recent:
        st.write("_No transactions found for the active filter._")
    else:
        for t in filtered_recent:
            meta = CATEGORIES.get(t.category, {})
            icon = meta.get("icon", "📦")
            badge_type = "income" if t.transaction_type == "income" else "expense"
            sign = "+" if t.transaction_type == "income" else "-"

            st.markdown(f"""
            <div style="background: rgba(19, 27, 46, 0.7); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 10px 16px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.4rem;">{icon}</span>
                <div>
                  <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">{t.description}</div>
                  <div style="font-size: 0.75rem; color: #94a3b8;">{t.transaction_date} • {t.payment_method} • <span class="badge badge-info">{t.category}</span></div>
                </div>
              </div>
              <div style="font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.1rem; color: {'#34d399' if t.transaction_type == 'income' else '#fb7185'};">
                {sign}{CURRENCY_SYMBOL}{t.amount:,.2f}
              </div>
            </div>
            """, unsafe_allow_html=True)


# ==================== PAGE 2: TRANSACTIONS MANAGEMENT ====================
elif nav_selection == "Transactions":
    st.subheader("💳 Transaction Management")

    # Search & Filter Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 2, 2])
    with f_col1:
        search_query = st.text_input("🔍 Search Description, Category, Merchant", placeholder="Search...")
    with f_col2:
        cat_filter = st.selectbox("Category", ["All"] + ALL_CATEGORIES)
    with f_col3:
        type_filter = st.selectbox("Type", ["All", "expense", "income"])
    with f_col4:
        sort_by = st.selectbox("Sort By", ["transaction_date DESC, id DESC", "amount DESC", "amount ASC", "category ASC"])

    tx_list = service.get_transactions(
        category=cat_filter,
        transaction_type=type_filter,
        search=search_query,
        order_by=sort_by
    )

    st.write(f"Showing **{len(tx_list)}** transactions")

    # Table & Edit/Delete
    if not tx_list:
        st.info("No transactions match your current filters.")
    else:
        # Display as interactive selectable rows
        for t in tx_list:
            col_icon, col_desc, col_cat, col_amt, col_edit, col_del = st.columns([0.5, 3.5, 2, 2, 1, 1])
            meta = CATEGORIES.get(t.category, {})
            icon = meta.get("icon", "📦")
            sign = "+" if t.transaction_type == "income" else "-"
            amt_color = "#34d399" if t.transaction_type == "income" else "#fb7185"

            with col_icon:
                st.markdown(f"<span style='font-size: 1.4rem;'>{icon}</span>", unsafe_allow_html=True)
            with col_desc:
                st.markdown(f"**{t.description}**  \n<span style='font-size: 0.75rem; color: #94a3b8;'>{t.transaction_date} • {t.payment_method}</span>", unsafe_allow_html=True)
            with col_cat:
                st.markdown(f"<span class='badge badge-info'>{t.category}</span>", unsafe_allow_html=True)
            with col_amt:
                st.markdown(f"<span style='font-family: JetBrains Mono; font-weight: 700; color: {amt_color};'>{sign}{CURRENCY_SYMBOL}{t.amount:,.2f}</span>", unsafe_allow_html=True)
            with col_edit:
                with st.popover("✏️ Edit"):
                    st.write(f"Edit Transaction #{t.id}")
                    new_desc = st.text_input("Description", value=t.description, key=f"desc_{t.id}")
                    new_amt = st.number_input("Amount", value=float(t.amount), min_value=0.01, step=50.0, key=f"amt_{t.id}")
                    cat_index = ALL_CATEGORIES.index(t.category) if t.category in ALL_CATEGORIES else 0
                    new_cat = st.selectbox("Category", ALL_CATEGORIES, index=cat_index, key=f"cat_{t.id}")
                    new_type = st.selectbox("Type", ["expense", "income"], index=0 if t.transaction_type == "expense" else 1, key=f"type_{t.id}")
                    new_date = st.date_input("Date", value=datetime.strptime(t.transaction_date, "%Y-%m-%d").date(), key=f"date_{t.id}")
                    learn_check = st.checkbox("Learn this category correction for future entries", value=True, key=f"learn_{t.id}")

                    if st.button("Save Changes", key=f"btn_save_{t.id}"):
                        updates = {
                            "description": new_desc,
                            "amount": new_amt,
                            "category": new_cat,
                            "transaction_type": new_type,
                            "transaction_date": new_date.isoformat(),
                        }
                        service.update_transaction(t.id, updates, learn_correction=learn_check)
                        st.success("Updated!")
                        st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_{t.id}", help="Delete transaction"):
                    service.delete_transaction(t.id)
                    st.rerun()


# ==================== PAGE 3: CATEGORIES DEEP DIVE ====================
elif nav_selection == "Categories":
    st.subheader(f"🏷️ Category Spending Breakdown • {calendar.month_name[selected_month]} {selected_year}")

    cat_df = analytics.get_category_breakdown()
    if cat_df.empty:
        st.info("No expense data recorded for this month.")
    else:
        for _, row in cat_df.iterrows():
            c_name = row["category"]
            c_tot = row["total_amount"]
            c_pct = row["percentage"]
            c_cnt = row["count"]
            meta = CATEGORIES.get(c_name, {})

            with st.expander(f"{meta.get('icon', '📦')} {c_name} — {CURRENCY_SYMBOL}{c_tot:,.2f} ({c_pct:.1f}% of total)"):
                st.write(f"**Description:** {meta.get('description', '')}")
                st.write(f"**Total Transactions:** {c_cnt}")
                st.write(f"**Average Cost per Transaction:** {CURRENCY_SYMBOL}{(c_tot / c_cnt):,.2f}")

                # Show category transactions
                c_txs = [t for t in period_transactions if t.category == c_name]
                if c_txs:
                    sub_records = [{"Date": t.transaction_date, "Description": t.description, "Amount": f"{CURRENCY_SYMBOL}{t.amount:,.2f}", "Payment": t.payment_method} for t in c_txs]
                    st.dataframe(pd.DataFrame(sub_records), use_container_width=True)


# ==================== PAGE 4: BUDGETS ====================
elif nav_selection == "Budgets":
    st.subheader(f"🎯 Monthly Budget Planner • {calendar.month_name[selected_month]} {selected_year}")

    b_data = budget_mgr.get_budget_status(selected_month, selected_year, period_transactions)

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        render_metric_card("Total Budget Limit", f"{CURRENCY_SYMBOL}{b_data['total_budget_limit']:,.2f}", "Configured Monthly Ceiling", "🎯", "Target", "info")
    with col_b2:
        render_metric_card("Actual Spending", f"{CURRENCY_SYMBOL}{b_data['total_actual_spent']:,.2f}", f"{b_data['overall_percentage']:.0f}% utilized", "💸", b_data['overall_status'].capitalize(), "expense" if b_data['overall_percentage'] > 100 else "income")
    with col_b3:
        render_metric_card("Remaining Buffer", f"{CURRENCY_SYMBOL}{b_data['total_remaining']:,.2f}", "Left to Spend", "🛡️", "Remaining", "income" if b_data['total_remaining'] >= 0 else "expense")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Set / Update Budget Form
    with st.expander("➕ Set or Update Category Budget", expanded=False):
        b_col_cat, b_col_limit, b_col_save = st.columns([3, 3, 2])
        with b_col_cat:
            target_cat = st.selectbox("Select Category", EXPENSE_CATEGORIES)
        with b_col_limit:
            target_limit = st.number_input("Monthly Limit (₹)", min_value=100.0, step=500.0, value=5000.0)
        with b_col_save:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Set Budget", type="primary", use_container_width=True):
                budget_mgr.set_category_budget(target_cat, target_limit, selected_month, selected_year)
                st.success(f"Budget for {target_cat} updated to {CURRENCY_SYMBOL}{target_limit:,.2f}!")
                st.rerun()

    st.markdown("### Category Budget Status")
    if not b_data["category_budgets"]:
        st.info("No category budgets set for this month. Use the form above to establish your limits!")
    else:
        for cb in b_data["category_budgets"]:
            col_bar, col_del = st.columns([9, 1])
            with col_bar:
                render_budget_progress(
                    category=cb["category"],
                    spent=cb["spent"],
                    limit=cb["limit"],
                    percentage=cb["percentage"],
                    status=cb["status"]
                )
            with col_del:
                st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_b_{cb['budget_id']}", help="Delete this budget"):
                    budget_mgr.delete_budget(cb["budget_id"])
                    st.rerun()


# ==================== PAGE 5: ANALYTICS & REPORTS ====================
elif nav_selection == "Analytics":
    st.subheader(f"📈 Advanced Financial Analytics & Reports • {calendar.month_name[selected_month]} {selected_year}")

    tab_overview, tab_recurring, tab_anomalies, tab_export = st.tabs([
        "📊 Trends & Visuals",
        "🔄 Recurring Expenses",
        "🚨 Unusual Spending",
        "📥 Analytical Report Export"
    ])

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Monthly Cash Flow (Income vs Expense)")
            flow_fig = all_analytics.create_monthly_trend_chart()
            st.plotly_chart(flow_fig, use_container_width=True)
        with c2:
            st.markdown("#### Daily Cumulative Spend Pattern")
            cum_fig = analytics.create_daily_trend_chart()
            st.plotly_chart(cum_fig, use_container_width=True)

    with tab_recurring:
        st.markdown("#### Identified Recurring Charges")
        st.caption("Automatically detected through repetition frequency and consistent amounts.")
        recurring = analytics.identify_recurring_expenses()
        if not recurring:
            st.info("No recurring expenses detected yet.")
        else:
            rec_df = pd.DataFrame(recurring)
            rec_df["average_amount"] = rec_df["average_amount"].apply(lambda x: f"{CURRENCY_SYMBOL}{x:,.2f}")
            rec_df["total_spent"] = rec_df["total_spent"].apply(lambda x: f"{CURRENCY_SYMBOL}{x:,.2f}")
            st.dataframe(rec_df, use_container_width=True)

    with tab_anomalies:
        st.markdown("#### Unusual Spending Anomaly Detection")
        st.caption("Statistical outliers flagged based on Interquartile Range (IQR) deviation.")
        anomalies = analytics.detect_unusual_spending()
        if not anomalies:
            st.success("✅ No unusual spending anomalies detected in this period.")
        else:
            for anom in anomalies:
                st.warning(f"**{anom['description']}** ({anom['category']}) on {anom['date']}: {anom['reason']}")

    with tab_export:
        st.markdown("#### Download Exportable Analytical Reports")
        st.write("Generate high-resolution PNG multi-panel charts and executive reports.")

        png_data = analytics.generate_matplotlib_report_image()
        st.download_button(
            label="🖼️ Download Matplotlib PNG Chart Report",
            data=png_data,
            file_name=f"expense_report_{selected_year}_{selected_month:02d}.png",
            mime="image/png",
            type="primary"
        )


# ==================== PAGE 6: AI INSIGHTS ====================
elif nav_selection == "AI Insights":
    st.subheader(f"💡 AI Financial Insights & Forecasts • {calendar.month_name[selected_month]} {selected_year}")
    st.caption("Derived mathematically from your stored transactions. Facts are strictly distinguished from estimates.")

    insights_list = insights_gen.generate_all_insights(selected_month, selected_year)

    if not insights_list:
        st.info("Record more transactions to unlock automated AI spending insights and projections!")
    else:
        for ins in insights_list:
            render_insight_card(ins)

    st.markdown("---")
    st.markdown("#### 📄 Executive Report Generator")
    md_report = generate_markdown_report(metrics, cat_df, insights_list, f"{calendar.month_name[selected_month]} {selected_year}")
    st.download_button(
        label="📥 Download Markdown Summary Report",
        data=md_report,
        file_name=f"executive_summary_{selected_year}_{selected_month:02d}.md",
        mime="text/markdown"
    )


# ==================== PAGE 7: SETTINGS & CSV ====================
elif nav_selection == "Settings & CSV":
    st.subheader("⚙️ Settings, Learned Corrections & Data Management")

    tab_learn, tab_csv, tab_ollama, tab_reset = st.tabs([
        "🧠 Learned Category Corrections",
        "📂 CSV Import / Export",
        "🤖 Ollama Connection",
        "⚠️ Reset Data"
    ])

    with tab_learn:
        st.markdown("#### User-Confirmed Category Corrections")
        st.caption("When you edit a transaction's category, the system learns your preference to auto-categorize future entries.")

        # Manual add
        with st.expander("➕ Add Custom Mapping"):
            m_col1, m_col2, m_col3 = st.columns([3, 3, 2])
            with m_col1:
                learn_term = st.text_input("Description / Merchant Keyword", placeholder="e.g. chaayos")
            with m_col2:
                learn_cat = st.selectbox("Assign to Category", ALL_CATEGORIES)
            with m_col3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Save Mapping", use_container_width=True):
                    if learn_term:
                        service.add_learned_mapping(learn_term, learn_cat)
                        st.success(f"Learned mapping for '{learn_term}' saved!")
                        st.rerun()

        mappings = service.get_learned_mappings()
        if not mappings:
            st.write("_No user corrections learned yet._")
        else:
            for m in mappings:
                c1, c2, c3 = st.columns([5, 3, 2])
                with c1:
                    st.write(f"**{m.normalized_description}**")
                with c2:
                    st.markdown(f"<span class='badge badge-info'>{m.category}</span>", unsafe_allow_html=True)
                with c3:
                    if st.button("🗑️ Delete", key=f"del_map_{m.id}"):
                        service.delete_learned_mapping(m.id)
                        st.rerun()

    with tab_csv:
        st.markdown("#### CSV Data Interchange")

        # Export CSV
        all_txs = service.get_transactions()
        csv_string = export_transactions_to_csv(all_txs)
        st.download_button(
            label="📥 Export All Transactions to CSV",
            data=csv_string,
            file_name=f"expenses_export_{date.today().isoformat()}.csv",
            mime="text/csv",
            type="primary"
        )

        st.markdown("---")
        st.markdown("#### Import Transactions from CSV")
        st.caption("Duplicate rows with matching date, amount, and description will be automatically detected and skipped.")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        if uploaded_file is not None:
            csv_content = uploaded_file.getvalue().decode("utf-8")
            if st.button("Process & Import CSV"):
                result = import_transactions_from_csv(csv_content, db, service.categorizer)
                st.success(f"Imported: {result['imported']} new transaction(s) • Skipped duplicates: {result['duplicates']}")
                if result["errors"]:
                    for err in result["errors"]:
                        st.warning(err)
                st.rerun()

    with tab_ollama:
        st.markdown("#### Local LLM (Ollama) Diagnostics")
        st.write(f"**Configured Base URL:** `{OLLAMA_BASE_URL}`")
        st.write(f"**Target Model:** `{OLLAMA_MODEL}`")

        if st.button("🧪 Test Ollama Connection"):
            try:
                import requests
                resp = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=3)
                if resp.status_code == 200:
                    models = [m.get("name") for m in resp.json().get("models", [])]
                    st.success(f"✅ Ollama service is active! Available models: {', '.join(models)}")
                else:
                    st.warning(f"Ollama returned status code: {resp.status_code}")
            except Exception as e:
                st.error(f"Could not connect to Ollama: {e}. (App will continue to operate normally with offline rule-based categorization).")

    with tab_reset:
        st.markdown("#### Danger Zone")
        st.warning("Clearing database will permanently delete all stored transactions, budgets, and learned mappings.")
        if st.button("⚠️ Delete All Stored Data", type="secondary"):
            with db.get_connection() as conn:
                conn.execute("DELETE FROM transactions")
                conn.execute("DELETE FROM budgets")
                conn.execute("DELETE FROM learned_mappings")
            st.success("Database wiped clean.")
            st.rerun()
