"""Create the portfolio Excel dashboard from the project's cleaned sales data."""

from __future__ import annotations

import sys
from datetime import datetime
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
        "filter_label": workbook.add_format({"bold": True, "font_size": 9, "font_color": COLORS["muted"], "bg_color": "#F8FAFC", "align": "center", **border}),
        "filter_value": workbook.add_format({"bold": True, "font_size": 10, "font_color": COLORS["text"], "bg_color": "#FFFFFF", "align": "center", "valign": "vcenter", **border}),
        "filter_date": workbook.add_format({"bold": True, "font_size": 10, "font_color": COLORS["text"], "bg_color": "#FFFFFF", "align": "center", "valign": "vcenter", "num_format": "dd mmm yyyy", **border}),
        "filter_note": workbook.add_format({"font_size": 9, "font_color": COLORS["muted"], "bg_color": "#F8FAFC", "italic": True, "align": "left", "valign": "vcenter", **border}),
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


def get_filter_criteria(extra_criteria: tuple[str, str] | None = None) -> str:
    """Return stable SUMIFS and COUNTIFS criteria for the selected filters."""
    criteria = [
        'CleanSalesData[order_date],">="&SelectedStartDate',
        'CleanSalesData[order_date],"<="&SelectedEndDate',
        'CleanSalesData[category],IF(SelectedCategory="All","*",SelectedCategory)',
        'CleanSalesData[sales_channel],IF(SelectedSalesChannel="All","*",SelectedSalesChannel)',
        'CleanSalesData[city],IF(SelectedCity="All","*",SelectedCity)',
        'CleanSalesData[product_name],IF(SelectedProduct="All","*",SelectedProduct)',
    ]
    if extra_criteria:
        dimension, value = extra_criteria
        criteria.append(f"CleanSalesData[{dimension}],{value}")
    return ",".join(criteria)


def get_kpi_formulas(df: pd.DataFrame) -> dict[str, str]:
    """Create Excel-native KPI formulas driven by the Dashboard selections."""
    criteria = get_filter_criteria()
    total_net_revenue = f"=SUMIFS(CleanSalesData[net_revenue],{criteria})"
    total_orders = f"=SUM(Filtered_Summary!$W$2:$W${df['order_id'].nunique() + 1})"
    total_customers = f"=SUM(Filtered_Summary!$T$2:$T${df['customer_id'].nunique() + 1})"
    total_units = f"=SUMIFS(CleanSalesData[quantity],{criteria})"
    gross_revenue = f"SUMIFS(CleanSalesData[gross_revenue],{criteria})"
    discount_amount = f"SUMIFS(CleanSalesData[discount_amount],{criteria})"
    return {
        "total_net_revenue": total_net_revenue,
        "total_orders": total_orders,
        "average_order_value": f'=IFERROR({total_net_revenue[1:]}/({total_orders[1:]}),0)',
        "total_customers": total_customers,
        "total_units_sold": total_units,
        "average_discount_rate": f"=IFERROR(({discount_amount})/({gross_revenue}),0)",
    }


def write_lists(writer: pd.ExcelWriter, df: pd.DataFrame, formats: dict[str, object]) -> dict[str, str]:
    """Write hidden dropdown values and return their Excel range references."""
    sheet = writer.book.add_worksheet("Lists")
    writer.sheets["Lists"] = sheet
    lists = {
        "dates": df["order_date"].drop_duplicates().sort_values().dt.to_pydatetime().tolist(),
        "categories": ["All", *sorted(df["category"].dropna().unique().tolist())],
        "sales_channels": ["All", *sorted(df["sales_channel"].dropna().unique().tolist())],
        "cities": ["All", *sorted(df["city"].dropna().unique().tolist())],
        "products": ["All", *sorted(df["product_name"].dropna().unique().tolist())],
    }
    headers = ["Dates", "Categories", "Sales Channels", "Cities", "Products"]
    sheet.write_row(0, 0, headers)
    references = {}
    for column, (key, values) in enumerate(lists.items()):
        for row, value in enumerate(values, start=1):
            if isinstance(value, datetime):
                sheet.write_datetime(row, column, value, formats["date"])
            else:
                sheet.write(row, column, value)
        references[key] = f"=Lists!${chr(65 + column)}$2:${chr(65 + column)}${len(values) + 1}"
    sheet.hide()
    return references


def write_filtered_summary(writer: pd.ExcelWriter, df: pd.DataFrame, formats: dict[str, object]) -> dict[str, tuple[int, int, int]]:
    """Write hidden filter-aware summary tables used by the Dashboard charts."""
    sheet = writer.book.add_worksheet("Filtered_Summary")
    writer.sheets["Filtered_Summary"] = sheet
    summary_specs = [
        ("monthly", "Month", sorted(df["order_month_period"].dropna().unique().tolist()), 0, "order_month_period"),
        ("category", "Category", sorted(df["category"].dropna().unique().tolist()), 3, "category"),
        ("channel", "Sales Channel", sorted(df["sales_channel"].dropna().unique().tolist()), 6, "sales_channel"),
        ("city", "City", sorted(df["city"].dropna().unique().tolist()), 9, "city"),
        ("product_all", "Product", sorted(df["product_name"].dropna().unique().tolist()), 12, "product_name"),
    ]
    locations = {}
    for key, label, values, column, dimension in summary_specs:
        sheet.write_row(0, column, [label, "Net Revenue"])
        for row, value in enumerate(values, start=1):
            sheet.write(row, column, value)
            formula = f"=SUMIFS(CleanSalesData[net_revenue],{get_filter_criteria((dimension, f'{sheet.name}!${chr(65 + column)}{row + 1}'))})"
            baseline = float(df.loc[df[dimension] == value, "net_revenue"].sum())
            sheet.write_formula(row, column + 1, formula, formats["currency"], baseline)
        locations[key] = (0, column, len(values))

    products = sorted(df["product_name"].dropna().unique().tolist())
    product_revenue = df.groupby("product_name")["net_revenue"].sum().to_dict()
    ranked_products = sorted(products, key=lambda product: (product_revenue[product], product), reverse=True)
    product_last_row = len(products) + 1
    sheet.write_row(0, 15, ["Top Product", "Net Revenue", "Rank Key"])
    for row in range(1, min(10, len(products)) + 1):
        excel_row = row + 1
        rank = row
        rank_key_formula = f"=LARGE($O$2:$O${product_last_row},{rank})"
        product_formula = f"=INDEX($M$2:$M${product_last_row},MATCH(R{excel_row},$O$2:$O${product_last_row},0))"
        revenue_formula = f"=INDEX($N$2:$N${product_last_row},MATCH(P{excel_row},$M$2:$M${product_last_row},0))"
        cached_product = ranked_products[row - 1]
        cached_revenue = float(product_revenue[cached_product])
        cached_rank_key = cached_revenue + (products.index(cached_product) + 2) / 1000000000
        sheet.write_formula(row, 17, rank_key_formula, None, cached_rank_key)
        sheet.write_formula(row, 15, product_formula, None, cached_product)
        sheet.write_formula(row, 16, revenue_formula, formats["currency"], cached_revenue)
    for row in range(1, len(products) + 1):
        cached_rank_key = float(product_revenue[products[row - 1]]) + (row + 1) / 1000000000
        sheet.write_formula(row, 14, f"=N{row + 1}+ROW()/1000000000", None, cached_rank_key)

    customers = sorted(df["customer_id"].dropna().unique().tolist())
    sheet.write_row(0, 18, ["Customer ID", "Included Customer"])
    for row, customer_id in enumerate(customers, start=1):
        sheet.write(row, 18, customer_id)
        formula = f'=--(COUNTIFS({get_filter_criteria(("customer_id", f"S{row + 1}"))})>0)'
        sheet.write_formula(row, 19, formula, formats["integer"], 1)

    orders = sorted(df["order_id"].dropna().unique().tolist())
    sheet.write_row(0, 21, ["Order ID", "Included Order"])
    for row, order_id in enumerate(orders, start=1):
        sheet.write(row, 21, order_id)
        formula = f'=--(COUNTIFS({get_filter_criteria(("order_id", f"V{row + 1}"))})>0)'
        sheet.write_formula(row, 22, formula, formats["integer"], 1)

    locations["products"] = (0, 15, min(10, len(products)))
    sheet.hide()
    return locations


def add_kpi_card(sheet, cell_range: str, label: str, formula: str, cached_value: float | int, label_format, value_format) -> None:
    """Add one KPI card to the Dashboard sheet."""
    start, end = cell_range.split(":")
    start_col, end_col, start_row = start[0], end[0], int(start[1:])
    sheet.merge_range(f"{start_col}{start_row}:{end_col}{start_row}", label, label_format)
    sheet.merge_range(f"{start_col}{start_row + 1}:{end_col}{start_row + 2}", "", value_format)
    sheet.write_formula(f"{start_col}{start_row + 1}", formula, value_format, cached_value)


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
        "categories": ["Filtered_Summary", first_row, start_col, last_row, start_col],
        "values": ["Filtered_Summary", first_row, start_col + 1, last_row, start_col + 1],
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


def write_dashboard(writer: pd.ExcelWriter, sheet, df: pd.DataFrame, locations, list_references, formats: dict[str, object]) -> None:
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
    sheet.print_area(0, 0, 66, 15)
    sheet.center_horizontally()
    sheet.merge_range("A1:P1", "Small Business Sales Dashboard", formats["title"])
    period = f"Reporting period: {df['order_date'].min():%d %b %Y} to {df['order_date'].max():%d %b %Y}"
    sheet.merge_range("A2:P2", period, formats["subtitle"])
    sheet.merge_range("A4:P4", "Interactive Filters", formats["section"])
    filter_controls = [
        ("A5:B5", "A6:B6", "START DATE", df["order_date"].min().to_pydatetime(), list_references["dates"], formats["filter_date"]),
        ("C5:D5", "C6:D6", "END DATE", df["order_date"].max().to_pydatetime(), list_references["dates"], formats["filter_date"]),
        ("E5:G5", "E6:G6", "CATEGORY", "All", list_references["categories"], formats["filter_value"]),
        ("H5:J5", "H6:J6", "SALES CHANNEL", "All", list_references["sales_channels"], formats["filter_value"]),
        ("K5:M5", "K6:M6", "CITY", "All", list_references["cities"], formats["filter_value"]),
        ("N5:P5", "N6:P6", "PRODUCT", "All", list_references["products"], formats["filter_value"]),
    ]
    for label_range, value_range, label, value, source, value_format in filter_controls:
        sheet.merge_range(label_range, label, formats["filter_label"])
        sheet.merge_range(value_range, value, value_format)
        sheet.data_validation(value_range.split(":")[0], {"validate": "list", "source": source})
    sheet.merge_range("A7:P7", "Change any dropdown selection to update the KPI cards and charts. Choose All to include every value in a category.", formats["filter_note"])
    kpis = calculate_kpis(df)
    kpi_formulas = get_kpi_formulas(df)
    cards = [
        ("A9:C11", "TOTAL NET REVENUE", kpi_formulas["total_net_revenue"], kpis["total_net_revenue"], formats["card_currency"]),
        ("D9:F11", "TOTAL ORDERS", kpi_formulas["total_orders"], kpis["total_orders"], formats["card_integer"]),
        ("G9:I11", "AVERAGE ORDER VALUE", kpi_formulas["average_order_value"], kpis["average_order_value"], formats["card_currency"]),
        ("J9:L11", "TOTAL CUSTOMERS", kpi_formulas["total_customers"], int(df["customer_id"].nunique()), formats["card_integer"]),
        ("M9:N11", "TOTAL UNITS SOLD", kpi_formulas["total_units_sold"], kpis["total_quantity_sold"], formats["card_integer"]),
        ("O9:P11", "AVERAGE DISCOUNT RATE", kpi_formulas["average_discount_rate"], kpis["discount_rate"], formats["card_percent"]),
    ]
    for cell_range, label, formula, cached_value, value_format in cards:
        add_kpi_card(sheet, cell_range, label, formula, cached_value, formats["card_label"], value_format)
    add_chart(workbook, sheet, locations, "monthly", "Monthly Net Revenue Trend", "line", "A14", COLORS["primary"])
    add_chart(workbook, sheet, locations, "category", "Revenue by Category", "bar", "I14", COLORS["primary"], major_unit=40000)
    add_chart(workbook, sheet, locations, "channel", "Revenue by Sales Channel", "doughnut", "A30")
    add_chart(workbook, sheet, locations, "products", "Top 10 Products by Revenue", "bar", "I30", COLORS["secondary"], major_unit=30000)
    add_chart(workbook, sheet, locations, "city", "Revenue by City", "bar", "A46", COLORS["primary_dark"], major_unit=20000)
    sheet.merge_range("I46:P46", "Key Business Insights (Overall Dataset)", formats["section"])
    for offset, insight in enumerate(generate_business_insights(df)[:6]):
        start_row = 47 + (offset * 3)
        sheet.merge_range(start_row - 1, 8, start_row + 1, 15, f"- {insight}", formats["insight"])
    sheet.merge_range("A67:P67", "Source: data/processed/small_business_sales_clean.csv | Revenue values are shown after discounts.", workbook.add_format({"font_size": 9, "font_color": COLORS["muted"], "italic": True}))


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
        writer.book.set_calc_mode("auto")
        writer.book.define_name("SelectedStartDate", "=Dashboard!$A$6")
        writer.book.define_name("SelectedEndDate", "=Dashboard!$C$6")
        writer.book.define_name("SelectedCategory", "=Dashboard!$E$6")
        writer.book.define_name("SelectedSalesChannel", "=Dashboard!$H$6")
        writer.book.define_name("SelectedCity", "=Dashboard!$K$6")
        writer.book.define_name("SelectedProduct", "=Dashboard!$N$6")
        dashboard = writer.book.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = dashboard
        write_clean_data(writer, df, formats)
        write_summary(writer, tables, formats)
        list_references = write_lists(writer, df, formats)
        locations = write_filtered_summary(writer, df, formats)
        write_dashboard(writer, dashboard, df, locations, list_references, formats)
        write_data_dictionary(writer, formats)
    return OUTPUT_PATH


if __name__ == "__main__":
    output_path = create_excel_dashboard()
    print(f"Excel dashboard created: {output_path.relative_to(PROJECT_ROOT)}")
