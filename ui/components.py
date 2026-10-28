"""
Streamlit UI custom component renderers with glassmorphism styling.
"""
from typing import Dict, Any, List, Optional
import streamlit as st
from src.config import CATEGORIES, CURRENCY_SYMBOL
from src.models import ParsedExpense


def render_metric_card(
    title: str,
    value: str,
    subtext: Optional[str] = None,
    icon: str = "💰",
    badge_text: Optional[str] = None,
    badge_type: str = "info"
) -> None:
    """Renders a modern glassmorphic financial metric card."""
    badge_html = f'<span class="badge badge-{badge_type}">{badge_text}</span>' if badge_text else ''
    subtext_html = f'<div class="metric-sub">{subtext}</div>' if subtext else ''

    html = f"""
    <div class="metric-card">
      <div class="metric-title">
        <span>{icon}</span>
        <span>{title}</span>
        <span style="margin-left: auto;">{badge_html}</span>
      </div>
      <div class="metric-value">{value}</div>
      {subtext_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_insight_card(insight: Dict[str, Any]) -> None:
    """Renders a structured insight card distinguishing facts from estimates."""
    severity = insight.get("severity", "info")
    icon = insight.get("icon", "💡")
    tag = insight.get("tag", "Observed Fact")
    title = insight.get("title", "Insight")
    message = insight.get("message", "")

    badge_class = "badge-info"
    if severity == "warning":
        badge_class = "badge-warning"
    elif severity == "danger":
        badge_class = "badge-expense"
    elif severity == "success":
        badge_class = "badge-income"

    html = f"""
    <div class="insight-card {severity}">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <div style="font-weight: 600; font-size: 0.95rem; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
          <span>{icon}</span>
          <span>{title}</span>
        </div>
        <span class="badge {badge_class}">{tag}</span>
      </div>
      <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">
        {message}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_budget_progress(category: str, spent: float, limit: float, percentage: float, status: str) -> None:
    """Renders visual budget progress meter with status indicator."""
    cat_meta = CATEGORIES.get(category, {})
    icon = cat_meta.get("icon", "📦")
    
    color_bar = "#10b981"
    badge_class = "badge-income"
    status_label = "Within Budget"

    if status == "exceeded":
        color_bar = "#f43f5e"
        badge_class = "badge-expense"
        status_label = "Over Budget"
    elif status == "warning":
        color_bar = "#f59e0b"
        badge_class = "badge-warning"
        status_label = "Approaching Limit"

    pct_display = min(percentage, 100)

    html = f"""
    <div style="background: rgba(19, 27, 46, 0.6); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 14px; margin-bottom: 12px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-weight: 600; font-size: 0.95rem; color: #f1f5f9; display: flex; align-items: center; gap: 6px;">
          <span>{icon}</span>
          <span>{category}</span>
        </span>
        <div>
          <span style="font-size: 0.85rem; color: #cbd5e1; font-family: 'JetBrains Mono', monospace;">
            {CURRENCY_SYMBOL}{spent:,.0f} / {CURRENCY_SYMBOL}{limit:,.0f}
          </span>
          <span class="badge {badge_class}" style="margin-left: 8px;">{status_label} ({percentage:.0f}%)</span>
        </div>
      </div>
      <div style="width: 100%; height: 8px; background: rgba(30, 41, 59, 0.8); border-radius: 999px; overflow: hidden;">
        <div style="width: {pct_display}%; height: 100%; background: {color_bar}; border-radius: 999px; transition: width 0.4s ease;"></div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
