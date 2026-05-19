"""
Utility functions for the Small Business Sales Dashboard.

This module contains the data loading, validation, filtering, KPI calculation,
aggregation, formatting, and basic business insight functions used by the
Streamlit dashboard.

The dashboard is based on the cleaned sales dataset from the project:
"Small Business Sales Data Cleaning & Analysis".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------
# Expected dataset columns
# ---------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "order_year",
    "order_month",
    "order_month_name",
    "order_month_period",
    "order_quarter",
    "customer_id",
    "customer_name",
    "city",
    "product_name",
    "category",
    "quantity",
    "unit_price",
    "discount_percent",
    "gross_revenue",
    "discount_amount",
    "net_revenue",
    "sales_channel",
    "payment_method",
    "has_discount",
]


# ---------------------------------------------------------------------
# Data loading and validation
# ---------------------------------------------------------------------

def validate_columns(df: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    """
    Validate whether the dataset contains all required columns.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset to validate.
    required_columns : list[str] | None
        List of required columns. If None, uses REQUIRED_COLUMNS.

    Raises
    ------
    ValueError
        If one or more required columns are missing.
    """
    required_columns = required_columns or REQUIRED_COLUMNS

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            "The dataset is missing the following required columns: "
            + ", ".join(missing_columns)
        )


def load_data(file_path: str | Path) -> pd.DataFrame:
    """
    Load and prepare the cleaned sales dataset.

    Parameters
    ----------
    file_path : str | Path
        Path to the cleaned CSV file.

    Returns
    -------
    pd.DataFrame
        Prepared sales dataset.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)

    validate_columns(df)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    numeric_columns = [
        "quantity",
        "unit_price",
        "discount_percent",
        "gross_revenue",
        "discount_amount",
        "net_revenue",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["has_discount"] = df["has_discount"].astype(bool)

    # Ensure the month period is correctly sorted in charts.
    df["order_month_period"] = df["order_date"].dt.to_period("M").astype(str)

    # Useful for time-series charts.
    df["month_start"] = df["order_date"].dt.to_period("M").dt.to_timestamp()

    return df


# ---------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------

def apply_filters(
    df: pd.DataFrame,
    start_date: Any | None = None,
    end_date: Any | None = None,
    categories: list[str] | None = None,
    products: list[str] | None = None,
    cities: list[str] | None = None,
    sales_channels: list[str] | None = None,
    payment_methods: list[str] | None = None,
    customers: list[str] | None = None,
    has_discount: bool | None = None,
) -> pd.DataFrame:
    """
    Apply dashboard filters to the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.
    start_date : Any | None
        Start date filter.
    end_date : Any | None
        End date filter.
    categories : list[str] | None
        Selected categories.
    products : list[str] | None
        Selected products.
    cities : list[str] | None
        Selected cities.
    sales_channels : list[str] | None
        Selected sales channels.
    payment_methods : list[str] | None
        Selected payment methods.
    customers : list[str] | None
        Selected customers.
    has_discount : bool | None
        If True, keeps only discounted orders.
        If False, keeps only non-discounted orders.
        If None, keeps all rows.

    Returns
    -------
    pd.DataFrame
        Filtered dataset.
    """
    filtered_df = df.copy()

    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        filtered_df = filtered_df[filtered_df["order_date"] >= start_date]

    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        filtered_df = filtered_df[filtered_df["order_date"] <= end_date]

    if categories:
        filtered_df = filtered_df[filtered_df["category"].isin(categories)]

    if products:
        filtered_df = filtered_df[filtered_df["product_name"].isin(products)]

    if cities:
        filtered_df = filtered_df[filtered_df["city"].isin(cities)]

    if sales_channels:
        filtered_df = filtered_df[filtered_df["sales_channel"].isin(sales_channels)]

    if payment_methods:
        filtered_df = filtered_df[filtered_df["payment_method"].isin(payment_methods)]

    if customers:
        filtered_df = filtered_df[filtered_df["customer_name"].isin(customers)]

    if has_discount is not None:
        filtered_df = filtered_df[filtered_df["has_discount"] == has_discount]

    return filtered_df


def get_filter_options(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Return sorted unique values for dashboard filters.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.

    Returns
    -------
    dict[str, list[str]]
        Dictionary with filter options.
    """
    return {
        "categories": sorted(df["category"].dropna().unique().tolist()),
        "products": sorted(df["product_name"].dropna().unique().tolist()),
        "cities": sorted(df["city"].dropna().unique().tolist()),
        "sales_channels": sorted(df["sales_channel"].dropna().unique().tolist()),
        "payment_methods": sorted(df["payment_method"].dropna().unique().tolist()),
        "customers": sorted(df["customer_name"].dropna().unique().tolist()),
    }


# ---------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------

def calculate_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """
    Calculate the main business KPIs for the dashboard.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.

    Returns
    -------
    dict[str, float | int]
        Dictionary containing the main KPIs.
    """
    if df.empty:
        return {
            "total_net_revenue": 0.0,
            "total_gross_revenue": 0.0,
            "total_orders": 0,
            "average_order_value": 0.0,
            "total_quantity_sold": 0,
            "total_discount_given": 0.0,
            "discount_rate": 0.0,
        }

    total_net_revenue = df["net_revenue"].sum()
    total_gross_revenue = df["gross_revenue"].sum()
    total_orders = df["order_id"].nunique()
    total_quantity_sold = df["quantity"].sum()
    total_discount_given = df["discount_amount"].sum()

    average_order_value = (
        total_net_revenue / total_orders if total_orders > 0 else 0.0
    )

    discount_rate = (
        total_discount_given / total_gross_revenue
        if total_gross_revenue > 0
        else 0.0
    )

    return {
        "total_net_revenue": total_net_revenue,
        "total_gross_revenue": total_gross_revenue,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
        "total_quantity_sold": int(total_quantity_sold),
        "total_discount_given": total_discount_given,
        "discount_rate": discount_rate,
    }


# ---------------------------------------------------------------------
# Aggregations for charts
# ---------------------------------------------------------------------

def get_monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales performance by month.

    Returns
    -------
    pd.DataFrame
        Monthly revenue, orders, quantity, and average order value.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "month_start",
                "order_month_period",
                "net_revenue",
                "gross_revenue",
                "discount_amount",
                "total_orders",
                "quantity_sold",
                "average_order_value",
            ]
        )

    monthly = (
        df.groupby(["month_start", "order_month_period"], as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("month_start")
    )

    monthly["average_order_value"] = (
        monthly["net_revenue"] / monthly["total_orders"]
    )

    return monthly


def get_category_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales performance by product category.

    Returns
    -------
    pd.DataFrame
        Category-level revenue, quantity, orders, discount rate, and AOV.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "category",
                "net_revenue",
                "gross_revenue",
                "discount_amount",
                "quantity_sold",
                "total_orders",
                "average_order_value",
                "discount_rate",
            ]
        )

    category = (
        df.groupby("category", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
            quantity_sold=("quantity", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .sort_values("net_revenue", ascending=False)
    )

    category["average_order_value"] = (
        category["net_revenue"] / category["total_orders"]
    )

    category["discount_rate"] = (
        category["discount_amount"] / category["gross_revenue"]
    ).fillna(0)

    return category


def get_top_products_by_revenue(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the top products by net revenue.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.
    top_n : int
        Number of products to return.

    Returns
    -------
    pd.DataFrame
        Top products by net revenue.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "product_name",
                "net_revenue",
                "quantity_sold",
                "total_orders",
                "average_order_value",
            ]
        )

    products = (
        df.groupby("product_name", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            quantity_sold=("quantity", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .sort_values("net_revenue", ascending=False)
        .head(top_n)
    )

    products["average_order_value"] = (
        products["net_revenue"] / products["total_orders"]
    )

    return products


def get_top_products_by_quantity(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the top products by quantity sold.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.
    top_n : int
        Number of products to return.

    Returns
    -------
    pd.DataFrame
        Top products by quantity sold.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "product_name",
                "quantity_sold",
                "net_revenue",
                "total_orders",
            ]
        )

    return (
        df.groupby("product_name", as_index=False)
        .agg(
            quantity_sold=("quantity", "sum"),
            net_revenue=("net_revenue", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .sort_values("quantity_sold", ascending=False)
        .head(top_n)
    )


def get_top_customers_by_revenue(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the top customers by net revenue.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.
    top_n : int
        Number of customers to return.

    Returns
    -------
    pd.DataFrame
        Top customers by net revenue.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "customer_name",
                "net_revenue",
                "total_orders",
                "quantity_sold",
                "average_order_value",
            ]
        )

    customers = (
        df.groupby(["customer_id", "customer_name"], as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("net_revenue", ascending=False)
        .head(top_n)
    )

    customers["average_order_value"] = (
        customers["net_revenue"] / customers["total_orders"]
    )

    return customers


def get_city_revenue(
    df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Return the top cities by net revenue.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.
    top_n : int
        Number of cities to return.

    Returns
    -------
    pd.DataFrame
        Top cities by net revenue.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "net_revenue",
                "total_orders",
                "quantity_sold",
                "average_order_value",
            ]
        )

    cities = (
        df.groupby("city", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("net_revenue", ascending=False)
        .head(top_n)
    )

    cities["average_order_value"] = cities["net_revenue"] / cities["total_orders"]

    return cities


def get_sales_channel_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales performance by sales channel.

    Returns
    -------
    pd.DataFrame
        Sales channel performance summary.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "sales_channel",
                "net_revenue",
                "total_orders",
                "quantity_sold",
                "average_order_value",
            ]
        )

    channels = (
        df.groupby("sales_channel", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("net_revenue", ascending=False)
    )

    channels["average_order_value"] = (
        channels["net_revenue"] / channels["total_orders"]
    )

    return channels


def get_payment_method_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales performance by payment method.

    Returns
    -------
    pd.DataFrame
        Payment method performance summary.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "payment_method",
                "net_revenue",
                "total_orders",
                "quantity_sold",
                "average_order_value",
            ]
        )

    payment = (
        df.groupby("payment_method", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("net_revenue", ascending=False)
    )

    payment["average_order_value"] = payment["net_revenue"] / payment["total_orders"]

    return payment


def get_discount_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare sales performance between discounted and non-discounted orders.

    Returns
    -------
    pd.DataFrame
        Discount status performance summary.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "has_discount",
                "net_revenue",
                "gross_revenue",
                "discount_amount",
                "total_orders",
                "quantity_sold",
                "discount_rate",
            ]
        )

    discount_summary = (
        df.groupby("has_discount", as_index=False)
        .agg(
            net_revenue=("net_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
            total_orders=("order_id", "nunique"),
            quantity_sold=("quantity", "sum"),
        )
        .sort_values("net_revenue", ascending=False)
    )

    discount_summary["discount_rate"] = (
        discount_summary["discount_amount"] / discount_summary["gross_revenue"]
    ).fillna(0)

    return discount_summary


def get_discount_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate discount performance by category.

    Returns
    -------
    pd.DataFrame
        Discount rate by category.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "category",
                "gross_revenue",
                "discount_amount",
                "net_revenue",
                "discount_rate",
            ]
        )

    discount = (
        df.groupby("category", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            discount_amount=("discount_amount", "sum"),
            net_revenue=("net_revenue", "sum"),
        )
        .sort_values("discount_amount", ascending=False)
    )

    discount["discount_rate"] = (
        discount["discount_amount"] / discount["gross_revenue"]
    ).fillna(0)

    return discount.sort_values("discount_rate", ascending=False)


# ---------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------

def format_currency(value: float, currency_symbol: str = "£") -> str:
    """
    Format a number as currency.

    Parameters
    ----------
    value : float
        Numeric value.
    currency_symbol : str
        Currency symbol to use.

    Returns
    -------
    str
        Formatted currency string.
    """
    return f"{currency_symbol}{value:,.2f}"


def format_number(value: float | int) -> str:
    """
    Format a number with thousands separator.

    Parameters
    ----------
    value : float | int
        Numeric value.

    Returns
    -------
    str
        Formatted number string.
    """
    return f"{value:,.0f}"


def format_percentage(value: float) -> str:
    """
    Format a decimal number as percentage.

    Parameters
    ----------
    value : float
        Decimal value. Example: 0.15 means 15%.

    Returns
    -------
    str
        Formatted percentage string.
    """
    return f"{value:.2%}"


# ---------------------------------------------------------------------
# Business insights
# ---------------------------------------------------------------------

def generate_business_insights(df: pd.DataFrame) -> list[str]:
    """
    Generate simple business insights based on the filtered dataset.

    These insights are intentionally simple and suitable for a first
    freelancer portfolio dashboard.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.

    Returns
    -------
    list[str]
        List of business insights.
    """
    if df.empty:
        return [
            "No data is available for the selected filters.",
            "Try changing the filters to include a wider period or more categories.",
        ]

    insights = []

    kpis = calculate_kpis(df)
    category_performance = get_category_performance(df)
    top_products = get_top_products_by_revenue(df, top_n=1)
    top_cities = get_city_revenue(df, top_n=1)
    sales_channels = get_sales_channel_performance(df)
    monthly_revenue = get_monthly_revenue(df)

    if not category_performance.empty:
        top_category = category_performance.iloc[0]
        category_share = top_category["net_revenue"] / kpis["total_net_revenue"]

        insights.append(
            f"The top-performing category is {top_category['category']}, "
            f"representing {category_share:.1%} of total net revenue."
        )

    if not top_products.empty:
        top_product = top_products.iloc[0]
        product_share = top_product["net_revenue"] / kpis["total_net_revenue"]

        insights.append(
            f"The highest-revenue product is {top_product['product_name']}, "
            f"representing {product_share:.1%} of total net revenue."
        )

    if not top_cities.empty:
        top_city = top_cities.iloc[0]
        city_share = top_city["net_revenue"] / kpis["total_net_revenue"]

        insights.append(
            f"The strongest city by revenue is {top_city['city']}, "
            f"representing {city_share:.1%} of total net revenue."
        )

    if not sales_channels.empty:
        top_channel = sales_channels.iloc[0]
        channel_share = top_channel["net_revenue"] / kpis["total_net_revenue"]

        insights.append(
            f"The leading sales channel is {top_channel['sales_channel']}, "
            f"representing {channel_share:.1%} of total net revenue."
        )

    if len(monthly_revenue) >= 2:
        first_month_revenue = monthly_revenue.iloc[0]["net_revenue"]
        last_month_revenue = monthly_revenue.iloc[-1]["net_revenue"]

        if first_month_revenue > 0:
            revenue_change = (
                last_month_revenue - first_month_revenue
            ) / first_month_revenue

            if revenue_change > 0:
                insights.append(
                    f"Net revenue increased by {revenue_change:.1%} from the first "
                    "month to the last month in the selected period."
                )
            elif revenue_change < 0:
                insights.append(
                    f"Net revenue decreased by {abs(revenue_change):.1%} from the first "
                    "month to the last month in the selected period."
                )
            else:
                insights.append(
                    "Net revenue remained stable from the first month to the last "
                    "month in the selected period."
                )

    if kpis["discount_rate"] > 0:
        insights.append(
            f"The overall discount rate is {kpis['discount_rate']:.1%}. "
            "The business should monitor whether discounts are increasing revenue "
            "or reducing margins unnecessarily."
        )

    return insights


def generate_business_recommendations(df: pd.DataFrame) -> list[str]:
    """
    Generate practical business recommendations based on sales performance.

    Parameters
    ----------
    df : pd.DataFrame
        Sales dataset.

    Returns
    -------
    list[str]
        List of practical recommendations.
    """
    if df.empty:
        return [
            "Review the selected filters because no data is available.",
        ]

    recommendations = []

    category_performance = get_category_performance(df)
    top_products = get_top_products_by_revenue(df, top_n=3)
    top_customers = get_top_customers_by_revenue(df, top_n=5)
    discount_by_category = get_discount_by_category(df)

    if not category_performance.empty:
        best_category = category_performance.iloc[0]["category"]
        recommendations.append(
            f"Prioritise stock, campaigns, and visibility for the strongest category: "
            f"{best_category}."
        )

    if not top_products.empty:
        product_names = ", ".join(top_products["product_name"].tolist())
        recommendations.append(
            f"Use the top revenue products as commercial anchors: {product_names}."
        )

    if not top_customers.empty:
        recommendations.append(
            "Create retention actions for the best customers, such as personalised "
            "offers, loyalty benefits, or early access to promotions."
        )

    if not discount_by_category.empty:
        highest_discount_category = discount_by_category.iloc[0]

        recommendations.append(
            f"Review the discount strategy for {highest_discount_category['category']}, "
            f"which has the highest discount rate at "
            f"{highest_discount_category['discount_rate']:.1%}."
        )

    recommendations.append(
        "Monitor monthly sales trends to identify seasonality, weak periods, and "
        "opportunities for targeted promotions."
    )

    return recommendations