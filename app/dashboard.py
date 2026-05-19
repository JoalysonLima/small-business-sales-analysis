"""
Streamlit dashboard for the Small Business Sales Data Cleaning & Analysis project.

This app turns the cleaned sales dataset into a simple business dashboard for
small business owners, sales managers, or freelance data analytics clients.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    apply_filters,
    calculate_kpis,
    format_currency,
    format_number,
    format_percentage,
    generate_business_insights,
    generate_business_recommendations,
    get_category_performance,
    get_city_revenue,
    get_discount_by_category,
    get_filter_options,
    get_monthly_revenue,
    get_payment_method_performance,
    get_sales_channel_performance,
    get_top_customers_by_revenue,
    get_top_products_by_quantity,
    get_top_products_by_revenue,
    load_data,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Small Business Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "small_business_sales_clean.csv"


# ---------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------

PRIMARY = "#0F766E"
PRIMARY_DARK = "#134E4A"
SECONDARY = "#2563EB"
BACKGROUND = "#F8FAFC"
CARD_BACKGROUND = "#FFFFFF"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
BORDER = "#E2E8F0"
WARNING = "#F97316"
NEGATIVE = "#DC2626"

CHART_COLORS = [
    "#0F766E",
    "#2563EB",
    "#14B8A6",
    "#64748B",
    "#F97316",
    "#475569",
    "#22C55E",
    "#06B6D4",
]


# ---------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BACKGROUND};
        }}

        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid {BORDER};
        }}

        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        h1, h2, h3 {{
            color: {TEXT_DARK};
            letter-spacing: -0.02em;
        }}

        .dashboard-header {{
            background: linear-gradient(135deg, {PRIMARY_DARK}, {PRIMARY});
            padding: 28px 32px;
            border-radius: 22px;
            color: white;
            margin-bottom: 24px;
            box-shadow: 0px 12px 32px rgba(15, 118, 110, 0.18);
        }}

        .dashboard-header h1 {{
            color: white;
            margin: 0;
            font-size: 2.1rem;
            font-weight: 750;
        }}

        .dashboard-header p {{
            color: rgba(255, 255, 255, 0.86);
            margin-top: 8px;
            margin-bottom: 0;
            font-size: 1rem;
            max-width: 860px;
        }}

        .header-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 18px;
        }}

        .header-pill {{
            background-color: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.22);
            color: white;
            padding: 7px 12px;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 500;
        }}

        .kpi-card {{
            background-color: {CARD_BACKGROUND};
            padding: 20px 20px;
            border-radius: 18px;
            border: 1px solid {BORDER};
            box-shadow: 0px 8px 24px rgba(15, 23, 42, 0.05);
            min-height: 135px;
        }}

        .kpi-label {{
            color: {TEXT_MUTED};
            font-size: 0.82rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0.045em;
            margin-bottom: 8px;
        }}

        .kpi-value {{
            color: {TEXT_DARK};
            font-size: 1.85rem;
            font-weight: 780;
            line-height: 1.15;
            margin-bottom: 8px;
        }}

        .kpi-description {{
            color: {TEXT_MUTED};
            font-size: 0.88rem;
            line-height: 1.35;
        }}

        .section-title {{
            color: {TEXT_DARK};
            font-size: 1.2rem;
            font-weight: 750;
            margin-top: 10px;
            margin-bottom: 8px;
        }}

        .section-subtitle {{
            color: {TEXT_MUTED};
            font-size: 0.92rem;
            margin-top: -4px;
            margin-bottom: 14px;
        }}

        .insight-card {{
            background-color: {CARD_BACKGROUND};
            border: 1px solid {BORDER};
            border-left: 5px solid {PRIMARY};
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0px 8px 24px rgba(15, 23, 42, 0.04);
            color: {TEXT_DARK};
            font-size: 0.95rem;
            line-height: 1.45;
        }}

        .recommendation-card {{
            background-color: #FFFDF7;
            border: 1px solid #FED7AA;
            border-left: 5px solid {WARNING};
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0px 8px 24px rgba(15, 23, 42, 0.04);
            color: {TEXT_DARK};
            font-size: 0.95rem;
            line-height: 1.45;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 18px;
        }}

        .stPlotlyChart {{
            background-color: white;
            border-radius: 18px;
        }}

        hr {{
            border: none;
            border-top: 1px solid {BORDER};
            margin: 1.5rem 0;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_sales_data(path: Path) -> pd.DataFrame:
    """
    Load the cleaned sales dataset with caching.
    """
    return load_data(path)


try:
    df = load_sales_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"Dataset not found at: {DATA_PATH}. "
        "Check whether the cleaned CSV file exists in data/processed/."
    )
    st.stop()
except ValueError as error:
    st.error(str(error))
    st.stop()


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def apply_plotly_layout(fig: go.Figure, height: int = 420) -> go.Figure:
    """
    Apply a consistent clean layout to Plotly charts.
    """
    fig.update_layout(
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=TEXT_DARK, family="Arial"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        title=dict(
            font=dict(size=18, color=TEXT_DARK),
            x=0,
            xanchor="left",
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_color=TEXT_DARK,
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )

    fig.update_yaxes(
        gridcolor="#EEF2F7",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )

    return fig


def render_kpi_card(label: str, value: str, description: str) -> None:
    """
    Render a custom KPI card.
    """
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str | None = None) -> None:
    """
    Render a section title and optional subtitle.
    """
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def format_date_range(data: pd.DataFrame) -> str:
    """
    Return the selected period as text.
    """
    if data.empty:
        return "No period selected"

    min_date = data["order_date"].min().strftime("%d %b %Y")
    max_date = data["order_date"].max().strftime("%d %b %Y")

    return f"{min_date} — {max_date}"


# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------

st.sidebar.markdown("## Filters")
st.sidebar.caption("Use the filters to explore specific business segments.")

filter_options = get_filter_options(df)

min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

selected_date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    selected_start_date, selected_end_date = selected_date_range
else:
    selected_start_date, selected_end_date = min_date, max_date

selected_categories = st.sidebar.multiselect(
    "Categories",
    options=filter_options["categories"],
)

selected_products = st.sidebar.multiselect(
    "Products",
    options=filter_options["products"],
)

selected_cities = st.sidebar.multiselect(
    "Cities",
    options=filter_options["cities"],
)

selected_channels = st.sidebar.multiselect(
    "Sales channels",
    options=filter_options["sales_channels"],
)

selected_payment_methods = st.sidebar.multiselect(
    "Payment methods",
    options=filter_options["payment_methods"],
)

discount_filter = st.sidebar.selectbox(
    "Discount status",
    options=["All orders", "Only discounted orders", "Only non-discounted orders"],
)

if discount_filter == "Only discounted orders":
    selected_discount_status = True
elif discount_filter == "Only non-discounted orders":
    selected_discount_status = False
else:
    selected_discount_status = None

st.sidebar.markdown("---")
st.sidebar.caption(
    "Tip: keep filters broad first, then narrow down to investigate specific patterns."
)


filtered_df = apply_filters(
    df=df,
    start_date=selected_start_date,
    end_date=selected_end_date,
    categories=selected_categories,
    products=selected_products,
    cities=selected_cities,
    sales_channels=selected_channels,
    payment_methods=selected_payment_methods,
    has_discount=selected_discount_status,
)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

period_text = format_date_range(filtered_df)

st.markdown(
    f"""
    <div class="dashboard-header">
        <h1>Small Business Sales Dashboard</h1>
        <p>
            A clean and practical sales performance dashboard designed for small
            businesses to monitor revenue, orders, products, customers, cities,
            channels, discounts, and commercial opportunities.
        </p>
        <div class="header-meta">
            <div class="header-pill">Period: {period_text}</div>
            <div class="header-pill">Dataset: Cleaned sales data</div>
            <div class="header-pill">Use case: Freelance business analytics</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if filtered_df.empty:
    st.warning("No data available for the selected filters. Adjust the filters and try again.")
    st.stop()


# ---------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------

kpis = calculate_kpis(filtered_df)

kpi_col_1, kpi_col_2, kpi_col_3 = st.columns(3)

with kpi_col_1:
    render_kpi_card(
        label="Total Net Revenue",
        value=format_currency(kpis["total_net_revenue"]),
        description="Revenue after discounts. This is the main sales performance indicator.",
    )

with kpi_col_2:
    render_kpi_card(
        label="Total Orders",
        value=format_number(kpis["total_orders"]),
        description="Number of unique orders in the selected period.",
    )

with kpi_col_3:
    render_kpi_card(
        label="Average Order Value",
        value=format_currency(kpis["average_order_value"]),
        description="Average revenue generated per order.",
    )

kpi_col_4, kpi_col_5, kpi_col_6 = st.columns(3)

with kpi_col_4:
    render_kpi_card(
        label="Quantity Sold",
        value=format_number(kpis["total_quantity_sold"]),
        description="Total number of units sold.",
    )

with kpi_col_5:
    render_kpi_card(
        label="Discount Given",
        value=format_currency(kpis["total_discount_given"]),
        description="Total discount amount applied to sales.",
    )

with kpi_col_6:
    render_kpi_card(
        label="Discount Rate",
        value=format_percentage(kpis["discount_rate"]),
        description="Discounts as a percentage of gross revenue.",
    )


st.markdown("<br>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Sales trend
# ---------------------------------------------------------------------

render_section_title(
    "Sales Trend",
    "Monthly net revenue helps identify growth, seasonality, and weak periods.",
)

monthly_revenue = get_monthly_revenue(filtered_df)

fig_monthly = go.Figure()

fig_monthly.add_trace(
    go.Scatter(
        x=monthly_revenue["month_start"],
        y=monthly_revenue["net_revenue"],
        mode="lines+markers",
        line=dict(color=PRIMARY, width=3),
        marker=dict(size=8, color=PRIMARY),
        fill="tozeroy",
        fillcolor="rgba(15, 118, 110, 0.12)",
        name="Net revenue",
        hovertemplate="<b>%{x|%b %Y}</b><br>Net revenue: £%{y:,.2f}<extra></extra>",
    )
)

fig_monthly.update_layout(
    title="Net Revenue Over Time",
    xaxis_title="Month",
    yaxis_title="Net revenue",
)

fig_monthly.update_yaxes(tickprefix="£", tickformat=",.0f")

fig_monthly = apply_plotly_layout(fig_monthly, height=430)

st.plotly_chart(fig_monthly, use_container_width=True)


# ---------------------------------------------------------------------
# Category and channel performance
# ---------------------------------------------------------------------

left_col, right_col = st.columns([1.2, 1])

with left_col:
    render_section_title(
        "Category Performance",
        "Shows which product categories generate the most revenue.",
    )

    category_performance = get_category_performance(filtered_df)

    fig_category = px.bar(
        category_performance.sort_values("net_revenue", ascending=True),
        x="net_revenue",
        y="category",
        orientation="h",
        text="net_revenue",
        color_discrete_sequence=[PRIMARY],
        title="Net Revenue by Category",
    )

    fig_category.update_traces(
        texttemplate="£%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Net revenue: £%{x:,.2f}<extra></extra>",
    )

    fig_category.update_layout(
        xaxis_title="Net revenue",
        yaxis_title="",
    )

    fig_category.update_xaxes(tickprefix="£", tickformat=",.0f")

    fig_category = apply_plotly_layout(fig_category, height=420)

    st.plotly_chart(fig_category, use_container_width=True)


with right_col:
    render_section_title(
        "Sales Channels",
        "Compares how much revenue each channel contributes.",
    )

    sales_channel_performance = get_sales_channel_performance(filtered_df)

    fig_channel = px.pie(
        sales_channel_performance,
        names="sales_channel",
        values="net_revenue",
        hole=0.62,
        color_discrete_sequence=CHART_COLORS,
        title="Revenue Share by Sales Channel",
    )

    fig_channel.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Net revenue: £%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )

    fig_channel.update_layout(
        showlegend=False,
        annotations=[
            dict(
                text="Revenue<br>Share",
                x=0.5,
                y=0.5,
                font_size=15,
                showarrow=False,
                font_color=TEXT_MUTED,
            )
        ],
    )

    fig_channel = apply_plotly_layout(fig_channel, height=420)

    st.plotly_chart(fig_channel, use_container_width=True)


# ---------------------------------------------------------------------
# Product rankings
# ---------------------------------------------------------------------

product_col_1, product_col_2 = st.columns(2)

with product_col_1:
    render_section_title(
        "Top Products by Revenue",
        "Products that bring the most money into the business.",
    )

    top_products_revenue = get_top_products_by_revenue(filtered_df, top_n=10)

    fig_top_products_revenue = px.bar(
        top_products_revenue.sort_values("net_revenue", ascending=True),
        x="net_revenue",
        y="product_name",
        orientation="h",
        text="net_revenue",
        color_discrete_sequence=[SECONDARY],
        title="Top 10 Products by Net Revenue",
    )

    fig_top_products_revenue.update_traces(
        texttemplate="£%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Net revenue: £%{x:,.2f}<extra></extra>",
    )

    fig_top_products_revenue.update_layout(
        xaxis_title="Net revenue",
        yaxis_title="",
    )

    fig_top_products_revenue.update_xaxes(tickprefix="£", tickformat=",.0f")

    fig_top_products_revenue = apply_plotly_layout(fig_top_products_revenue, height=460)

    st.plotly_chart(fig_top_products_revenue, use_container_width=True)


with product_col_2:
    render_section_title(
        "Top Products by Quantity",
        "Best-selling products by number of units sold.",
    )

    top_products_quantity = get_top_products_by_quantity(filtered_df, top_n=10)

    fig_top_products_quantity = px.bar(
        top_products_quantity.sort_values("quantity_sold", ascending=True),
        x="quantity_sold",
        y="product_name",
        orientation="h",
        text="quantity_sold",
        color_discrete_sequence=["#14B8A6"],
        title="Top 10 Products by Quantity Sold",
    )

    fig_top_products_quantity.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Quantity sold: %{x:,.0f}<extra></extra>",
    )

    fig_top_products_quantity.update_layout(
        xaxis_title="Quantity sold",
        yaxis_title="",
    )

    fig_top_products_quantity = apply_plotly_layout(fig_top_products_quantity, height=460)

    st.plotly_chart(fig_top_products_quantity, use_container_width=True)


# ---------------------------------------------------------------------
# Geography and customer performance
# ---------------------------------------------------------------------

geo_col, customer_col = st.columns(2)

with geo_col:
    render_section_title(
        "Top Cities",
        "Cities with the highest revenue contribution.",
    )

    city_revenue = get_city_revenue(filtered_df, top_n=10)

    fig_city = px.bar(
        city_revenue.sort_values("net_revenue", ascending=True),
        x="net_revenue",
        y="city",
        orientation="h",
        text="net_revenue",
        color_discrete_sequence=[PRIMARY_DARK],
        title="Top Cities by Net Revenue",
    )

    fig_city.update_traces(
        texttemplate="£%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Net revenue: £%{x:,.2f}<extra></extra>",
    )

    fig_city.update_layout(
        xaxis_title="Net revenue",
        yaxis_title="",
    )

    fig_city.update_xaxes(tickprefix="£", tickformat=",.0f")

    fig_city = apply_plotly_layout(fig_city, height=440)

    st.plotly_chart(fig_city, use_container_width=True)


with customer_col:
    render_section_title(
        "Top Customers",
        "Customers generating the most revenue.",
    )

    top_customers = get_top_customers_by_revenue(filtered_df, top_n=10)

    fig_customers = px.bar(
        top_customers.sort_values("net_revenue", ascending=True),
        x="net_revenue",
        y="customer_name",
        orientation="h",
        text="net_revenue",
        color_discrete_sequence=["#475569"],
        title="Top Customers by Net Revenue",
    )

    fig_customers.update_traces(
        texttemplate="£%{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Net revenue: £%{x:,.2f}<extra></extra>",
    )

    fig_customers.update_layout(
        xaxis_title="Net revenue",
        yaxis_title="",
    )

    fig_customers.update_xaxes(tickprefix="£", tickformat=",.0f")

    fig_customers = apply_plotly_layout(fig_customers, height=440)

    st.plotly_chart(fig_customers, use_container_width=True)


# ---------------------------------------------------------------------
# Discounts and payment method
# ---------------------------------------------------------------------

discount_col, payment_col = st.columns([1.2, 1])

with discount_col:
    render_section_title(
        "Discount Analysis",
        "Highlights categories where discounts may be affecting revenue quality.",
    )

    discount_by_category = get_discount_by_category(filtered_df)

    fig_discount = px.bar(
        discount_by_category.sort_values("discount_rate", ascending=True),
        x="discount_rate",
        y="category",
        orientation="h",
        text="discount_rate",
        color_discrete_sequence=[WARNING],
        title="Discount Rate by Category",
    )

    fig_discount.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Discount rate: %{x:.2%}<extra></extra>",
    )

    fig_discount.update_layout(
        xaxis_title="Discount rate",
        yaxis_title="",
    )

    fig_discount.update_xaxes(tickformat=".0%")

    fig_discount = apply_plotly_layout(fig_discount, height=410)

    st.plotly_chart(fig_discount, use_container_width=True)


with payment_col:
    render_section_title(
        "Payment Methods",
        "Shows which payment methods are most associated with revenue.",
    )

    payment_performance = get_payment_method_performance(filtered_df)

    fig_payment = px.pie(
        payment_performance,
        names="payment_method",
        values="net_revenue",
        hole=0.62,
        color_discrete_sequence=CHART_COLORS,
        title="Revenue Share by Payment Method",
    )

    fig_payment.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Net revenue: £%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )

    fig_payment.update_layout(
        showlegend=False,
        annotations=[
            dict(
                text="Payment<br>Mix",
                x=0.5,
                y=0.5,
                font_size=15,
                showarrow=False,
                font_color=TEXT_MUTED,
            )
        ],
    )

    fig_payment = apply_plotly_layout(fig_payment, height=410)

    st.plotly_chart(fig_payment, use_container_width=True)


# ---------------------------------------------------------------------
# Insights and recommendations
# ---------------------------------------------------------------------

st.markdown("---")

insight_col, recommendation_col = st.columns(2)

with insight_col:
    render_section_title(
        "Key Business Insights",
        "Main observations generated from the selected data.",
    )

    insights = generate_business_insights(filtered_df)

    for insight in insights:
        st.markdown(
            f"""
            <div class="insight-card">
                {insight}
            </div>
            """,
            unsafe_allow_html=True,
        )


with recommendation_col:
    render_section_title(
        "Practical Recommendations",
        "Actions the business could consider based on the dashboard.",
    )

    recommendations = generate_business_recommendations(filtered_df)

    for recommendation in recommendations:
        st.markdown(
            f"""
            <div class="recommendation-card">
                {recommendation}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.markdown("---")

st.caption(
    "Dashboard built with Streamlit, Pandas, and Plotly. "
    "Designed as a freelance-style business analytics deliverable."
)