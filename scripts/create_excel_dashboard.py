"""Create the portfolio Excel dashboard from the project's cleaned sales data."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "small_business_sales_clean.csv"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "excel" / "small_business_sales_dashboard.xlsx"
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from utils import (  # noqa: E402
    calculate_kpis,
    generate_business_insights,
    get_category_performance,
    get_city_revenue,
    get_discount_by_category,
    get_monthly_revenue,
    get_sales_channel_performance,
    get_top_customers_by_revenue,
    get_top_products_by_revenue,
    load_data,
)

COLORS = {
    "primary": "#0F766E",
    "primary_dark": "#134E4A",
    "secondary": "#2563EB",
    "card": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "#E2E8F0",
}
GBP_FORMAT = "\u00a3#,##0.00"
GBP_ROUNDED_FORMAT = "\u00a3#,##0"

DATA_DICTIONARY = [
    ("order_id", "Unique identifier for each sales order."),
    ("order_date", "Date when the order was placed."),
    ("order_year", "Calendar year of the order."),
    ("order_month", "Numeric month of the order, from 1 to 12."),
    ("order_month_name", "Month name for easier reporting."),
    ("order_month_period", "Year and month reporting period in YYYY-MM format."),
    ("order_quarter", "Calendar quarter of the order, from 1 to 4."),
    ("customer_id", "Unique identifier for the customer."),
    ("customer_name", "Customer name used for customer-level reporting."),
    ("city", "Customer or order city used for location analysis."),
    ("product_name", "Product sold in the transaction."),
    ("category", "Product category used to group related products."),
    ("quantity", "Number of units sold in the transaction."),
    ("unit_price", "Selling price per unit before discounts."),
    ("discount_percent", "Discount percentage applied to the transaction."),
    ("gross_revenue", "Sales value before discounts."),
    ("discount_amount", "Currency value deducted through discounts."),
    ("net_revenue", "Sales value after discounts."),
    ("sales_channel", "Channel where the sale happened, such as store or online."),
    ("payment_method", "Payment option used by the customer."),
    ("has_discount", "Indicates whether a discount was applied."),
]


def build_summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Prepare the reporting tables used by the Summary and Dashboard sheets."""
    return {
        "monthly": get_monthly_revenue(df)[
            ["order_month_period", "net_revenue", "total_orders", "quantity_sold", "average_order_value"]
        ].rename(columns={
            "order_month_period": "Month", "net_revenue": "Net Revenue",
            "total_orders": "Total Orders", "quantity_sold": "Units Sold",
            "average_order_value": "Average Order Value",
        }),
        "category": get_category_performance(df)[
            ["category", "net_revenue", "total_orders", "quantity_sold", "average_order_value"]
        ].rename(columns={
            "category": "Category", "net_revenue": "Net Revenue",
            "total_orders": "Total Orders", "quantity_sold": "Units Sold",
            "average_order_value": "Average Order Value",
        }),
        "channel": get_sales_channel_performance(df)[
            ["sales_channel", "net_revenue", "total_orders", "quantity_sold", "average_order_value"]
        ].rename(columns={
            "sales_channel": "Sales Channel", "net_revenue": "Net Revenue",
            "total_orders": "Total Orders", "quantity_sold": "Units Sold",
            "average_order_value": "Average Order Value",
        }),
        "city": get_city_revenue(df, top_n=df["city"].nunique())[
            ["city", "net_revenue", "total_orders", "quantity_sold", "average_order_value"]
        ].rename(columns={
            "city": "City", "net_revenue": "Net Revenue", "total_orders": "Total Orders",
            "quantity_sold": "Units Sold", "average_order_value": "Average Order Value",
        }),
        "products": get_top_products_by_revenue(df, top_n=10)[
            ["product_name", "net_revenue", "quantity_sold", "total_orders", "average_order_value"]
        ].rename(columns={
            "product_name": "Product", "net_revenue": "Net Revenue",
            "quantity_sold": "Units Sold", "total_orders": "Total Orders",
            "average_order_value": "Average Order Value",
        }),
        "customers": get_top_customers_by_revenue(df, top_n=10)[
            ["customer_id", "customer_name", "net_revenue", "total_orders", "quantity_sold", "average_order_value"]
        ].rename(columns={
            "customer_id": "Customer ID", "customer_name": "Customer Name",
            "net_revenue": "Net Revenue", "total_orders": "Total Orders",
            "quantity_sold": "Units Sold", "average_order_value": "Average Order Value",
        }),
        "discount": get_discount_by_category(df)[
            ["category", "gross_revenue", "discount_amount", "net_revenue", "discount_rate"]
        ].rename(columns={
            "category": "Category", "gross_revenue": "Gross Revenue",
            "discount_amount": "Discount Amount", "net_revenue": "Net Revenue",
            "discount_rate": "Average Discount Rate",
        }),
    }


def create_formats(workbook) -> dict[str, object]:
    """Create reusable workbook formats."""
    border = {"border": 1, "border_color": COLORS["border"]}
    return {
        "title": workbook.add_format({"bold": True, "font_size": 22, "font_color": "#FFFFFF", "bg_color": COLORS["primary_dark"]}),
        "subtitle": workbook.add_format({"font_size": 11, "font_color": "#D1FAE5", "bg_color": COLORS["primary_dark"]}),
        "section": workbook.add_format({"bold": True, "font_size": 12, "font_color": "#FFFFFF", "bg_color": COLORS["primary"]}),
        "card_label": workbook.add_format({"bold": True, "font_size": 10, "font_color": COLORS["muted"], "bg_color": COLORS["card"], "align": "center", **border}),
        "card_currency": workbook.add_format({"bold": True, "font_size": 17, "font_color": COLORS["text"], "bg_color": COLORS["card"], "align": "center", "valign": "vcenter", "num_format": GBP_FORMAT, **border}),
        "card_integer": workbook.add_format({"bold": True, "font_size": 17, "font_color": COLORS["text"], "bg_color": COLORS["card"], "align": "center", "valign": "vcenter", "num_format": "#,##0", **border}),
        "card_percent": workbook.add_format({"bold": True, "font_size": 17, "font_color": COLORS["text"], "bg_color": COLORS["card"], "align": "center", "valign": "vcenter", "num_format": "0.00%", **border}),
        "currency": workbook.add_format({"num_format": GBP_FORMAT}),
        "percent": workbook.add_format({"num_format": "0.00%"}),
        "integer": workbook.add_format({"num_format": "#,##0"}),
        "date": workbook.add_format({"num_format": "dd mmm yyyy"}),
        "insight": workbook.add_format({"font_size": 10, "font_color": COLORS["text"], "bg_color": "#F0FDFA", "text_wrap": True, "valign": "vcenter", **border}),
        "dictionary": workbook.add_format({"text_wrap": True, "valign": "top"}),
    }


def write_clean_data(writer: pd.ExcelWriter, df: pd.DataFrame, formats: dict[str, object]) -> None:
    """Write the cleaned dataset as an Excel table with business-friendly formats."""
    clean = df.drop(columns=["month_start"], errors="ignore").copy()
    clean["discount_percent"] = clean["discount_percent"] / 100
    clean.to_excel(writer, sheet_name="Clean_Data", index=False)
    sheet = writer.sheets["Clean_Data"]
    sheet.freeze_panes(1, 0)
    sheet.add_table(0, 0, len(clean), len(clean.columns) - 1, {
        "name": "CleanSalesData", "style": "Table Style Medium 2",
        "columns": [{"header": column} for column in clean.columns],
    })
    widths = {
        "order_id": 14, "order_date": 13, "order_month_name": 15,
        "order_month_period": 18, "customer_id": 14, "customer_name": 20,
        "city": 14, "product_name": 20, "category": 15,
        "sales_channel": 18, "payment_method": 17,
    }
    for index, column in enumerate(clean.columns):
        cell_format = None
        if column == "order_date":
            cell_format = formats["date"]
        elif column in {"unit_price", "gross_revenue", "discount_amount", "net_revenue"}:
            cell_format = formats["currency"]
        elif column == "discount_percent":
            cell_format = formats["percent"]
        elif column in {"quantity", "order_year", "order_month", "order_quarter"}:
            cell_format = formats["integer"]
        sheet.set_column(index, index, widths.get(column, max(11, min(16, len(column) + 2))), cell_format)


def write_summary(writer: pd.ExcelWriter, tables: dict[str, pd.DataFrame], formats: dict[str, object]) -> dict[str, tuple[int, int, int]]:
    """Write summary tables and return their locations for chart references."""
    sheet = writer.book.add_worksheet("Summary")
    writer.sheets["Summary"] = sheet
    sheet.hide_gridlines(2)
    sheet.freeze_panes(3, 0)
    sheet.merge_range("A1:M1", "Sales Performance Summary Tables", formats["title"])
    sheet.merge_range("A2:M2", "Aggregated views used by the executive Excel dashboard", formats["subtitle"])
    sections = [
        ("monthly", "Monthly Net Revenue", 3, 0, "MonthlyRevenue"),
        ("category", "Revenue by Category", 3, 7, "CategoryRevenue"),
        ("channel", "Revenue by Sales Channel", 20, 0, "ChannelRevenue"),
        ("city", "Revenue by City", 20, 7, "CityRevenue"),
        ("products", "Top 10 Products by Revenue", 29, 0, "TopProductsRevenue"),
        ("customers", "Top 10 Customers by Revenue", 43, 0, "TopCustomersRevenue"),
        ("discount", "Average Discount by Category", 43, 7, "CategoryDiscount"),
    ]
    locations = {}
    for key, title, row, col, table_name in sections:
        frame = tables[key]
        sheet.merge_range(row, col, row, col + len(frame.columns) - 1, title, formats["section"])
        frame.to_excel(writer, sheet_name="Summary", startrow=row + 1, startcol=col, index=False)
        sheet.add_table(row + 1, col, row + len(frame) + 1, col + len(frame.columns) - 1, {
            "name": table_name, "style": "Table Style Medium 2",
            "columns": [{"header": column} for column in frame.columns],
        })
        for offset, column in enumerate(frame.columns):
            cell_format = None
            if "Revenue" in column or column in {"Average Order Value", "Discount Amount"}:
                cell_format = formats["currency"]
            elif "Rate" in column:
                cell_format = formats["percent"]
            elif column in {"Total Orders", "Units Sold"}:
                cell_format = formats["integer"]
            sheet.set_column(col + offset, col + offset, max(15, min(22, len(column) + 3)), cell_format)
        locations[key] = (row + 1, col, len(frame))
    return locations


def add_kpi_card(sheet, cell_range: str, label: str, value: float | int, label_format, value_format) -> None:
    """Add one KPI card to the Dashboard sheet."""
    start, end = cell_range.split(":")
    start_col, end_col, start_row = start[0], end[0], int(start[1:])
    sheet.merge_range(f"{start_col}{start_row}:{end_col}{start_row}", label, label_format)
    sheet.merge_range(f"{start_col}{start_row + 1}:{end_col}{start_row + 2}", value, value_format)


def add_chart(
    workbook,
    sheet,
    locations,
    key: str,
    title: str,
    chart_type: str,
    position: str,
    color: str | None = None,
    major_unit: int | None = None,
) -> None:
    """Add a consistently styled chart linked to a Summary table."""
    header_row, start_col, rows = locations[key]
    first_row, last_row = header_row + 1, header_row + rows
    chart = workbook.add_chart({"type": chart_type})
    series = {
        "name": title,
        "categories": ["Summary", first_row, start_col, last_row, start_col],
        "values": ["Summary", first_row, start_col + 1, last_row, start_col + 1],
    }
    if color:
        series["fill"] = {"color": color}
        series["line"] = {"color": color}
    if chart_type == "line":
        series["marker"] = {"type": "circle", "size": 5, "border": {"color": color}, "fill": {"color": color}}
        series["line"] = {"color": color, "width": 2.5}
    if chart_type == "bar":
        series["data_labels"] = {"value": True, "num_format": GBP_ROUNDED_FORMAT, "position": "outside_end"}
    chart.add_series(series)
    chart.set_title({"name": title, "name_font": {"size": 12, "bold": True, "color": COLORS["text"]}})
    chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
    chart.set_plotarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
    chart.set_legend({"none": True})
    if chart_type == "bar":
        chart.set_x_axis({
            "num_format": GBP_ROUNDED_FORMAT,
            "major_unit": major_unit,
            "major_gridlines": {"visible": False},
        })
        chart.set_y_axis({"reverse": True, "interval_unit": 1, "major_gridlines": {"visible": False}})
    elif chart_type == "line":
        chart.set_y_axis({"num_format": GBP_ROUNDED_FORMAT, "major_gridlines": {"visible": True, "line": {"color": COLORS["border"]}}})
        chart.set_x_axis({"major_gridlines": {"visible": False}})
    elif chart_type == "doughnut":
        chart.set_hole_size(62)
        chart.set_legend({"position": "bottom"})
    sheet.insert_chart(position, chart, {"x_scale": 1.12, "y_scale": 0.70})


def write_dashboard(writer: pd.ExcelWriter, sheet, df: pd.DataFrame, locations, formats: dict[str, object]) -> None:
    """Create the executive Dashboard sheet."""
    workbook = writer.book
    sheet.hide_gridlines(2)
    sheet.set_tab_color(COLORS["primary"])
    sheet.set_column("A:P", 12)
    sheet.set_row(0, 32)
    sheet.set_landscape()
    sheet.set_paper(9)
    sheet.fit_to_pages(1, 1)
    sheet.set_margins(left=0.25, right=0.25, top=0.35, bottom=0.35)
    sheet.print_area(0, 0, 60, 15)
    sheet.center_horizontally()
    sheet.merge_range("A1:P1", "Small Business Sales Dashboard", formats["title"])
    period = f"Reporting period: {df['order_date'].min():%d %b %Y} to {df['order_date'].max():%d %b %Y}"
    sheet.merge_range("A2:P2", period, formats["subtitle"])
    kpis = calculate_kpis(df)
    cards = [
        ("A4:C6", "TOTAL NET REVENUE", kpis["total_net_revenue"], formats["card_currency"]),
        ("D4:F6", "TOTAL ORDERS", kpis["total_orders"], formats["card_integer"]),
        ("G4:I6", "AVERAGE ORDER VALUE", kpis["average_order_value"], formats["card_currency"]),
        ("J4:L6", "TOTAL CUSTOMERS", int(df["customer_id"].nunique()), formats["card_integer"]),
        ("M4:N6", "TOTAL UNITS SOLD", kpis["total_quantity_sold"], formats["card_integer"]),
        ("O4:P6", "AVERAGE DISCOUNT RATE", kpis["discount_rate"], formats["card_percent"]),
    ]
    for cell_range, label, value, value_format in cards:
        add_kpi_card(sheet, cell_range, label, value, formats["card_label"], value_format)
    add_chart(workbook, sheet, locations, "monthly", "Monthly Net Revenue Trend", "line", "A9", COLORS["primary"])
    add_chart(workbook, sheet, locations, "category", "Revenue by Category", "bar", "I9", COLORS["primary"], major_unit=40000)
    add_chart(workbook, sheet, locations, "channel", "Revenue by Sales Channel", "doughnut", "A25")
    add_chart(workbook, sheet, locations, "products", "Top 10 Products by Revenue", "bar", "I25", COLORS["secondary"], major_unit=30000)
    add_chart(workbook, sheet, locations, "city", "Revenue by City", "bar", "A41", COLORS["primary_dark"], major_unit=20000)
    sheet.merge_range("I41:P41", "Key Business Insights", formats["section"])
    for offset, insight in enumerate(generate_business_insights(df)[:6]):
        start_row = 42 + (offset * 3)
        sheet.merge_range(start_row - 1, 8, start_row + 1, 15, f"- {insight}", formats["insight"])
    sheet.merge_range("A61:P61", "Source: data/processed/small_business_sales_clean.csv | Revenue values are shown after discounts.", workbook.add_format({"font_size": 9, "font_color": COLORS["muted"], "italic": True}))


def write_data_dictionary(writer: pd.ExcelWriter, formats: dict[str, object]) -> None:
    """Write simple business definitions for the cleaned dataset columns."""
    sheet = writer.book.add_worksheet("Data_Dictionary")
    writer.sheets["Data_Dictionary"] = sheet
    sheet.hide_gridlines(2)
    for row, values in enumerate([("Column", "Business Meaning"), *DATA_DICTIONARY]):
        sheet.write_row(row, 0, values, formats["dictionary"])
    sheet.add_table(0, 0, len(DATA_DICTIONARY), 1, {
        "name": "DataDictionary", "style": "Table Style Medium 2",
        "columns": [{"header": "Column"}, {"header": "Business Meaning"}],
    })
    sheet.freeze_panes(1, 0)
    sheet.set_column("A:A", 24)
    sheet.set_column("B:B", 86)
    sheet.set_default_row(22)


def create_excel_dashboard() -> Path:
    """Build and save the complete Excel dashboard workbook."""
    df = load_data(DATA_PATH)
    tables = build_summary_tables(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter", datetime_format="dd mmm yyyy") as writer:
        formats = create_formats(writer.book)
        dashboard = writer.book.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = dashboard
        write_clean_data(writer, df, formats)
        locations = write_summary(writer, tables, formats)
        write_dashboard(writer, dashboard, df, locations, formats)
        write_data_dictionary(writer, formats)
    return OUTPUT_PATH


if __name__ == "__main__":
    output_path = create_excel_dashboard()
    print(f"Excel dashboard created: {output_path.relative_to(PROJECT_ROOT)}")
