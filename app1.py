import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_data

# 1. Page Configuration

st.set_page_config(
    page_title="Electronics Sales Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Electronics Sales Intelligence Dashboard")
st.caption(
    "End-to-End Data Analytics Dashboard | "
    "PostgreSQL | Python | Streamlit | Plotly"
)

st.divider()


# 2. Get Data Date Range

date_range_query = """
SELECT
    MIN(order_date)::date AS min_date,
    MAX(order_date)::date AS max_date
FROM staging.electronics_sales;
"""

date_range = get_data(date_range_query)

min_date = date_range.loc[0, "min_date"]
max_date = date_range.loc[0, "max_date"]



# 3. Sidebar Filters

st.sidebar.header("Dashboard Filters")

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(selected_dates) != 2:
    st.warning("Please select a start date and end date.")
    st.stop()

start_date, end_date = selected_dates

if start_date > end_date:
    st.error("Start date cannot be later than end date.")
    st.stop()

params = {
    "start_date": start_date,
    "end_date": end_date
}

st.sidebar.markdown("--")
st.sidebar.caption(
    f"Selected period: {start_date} to {end_date}"
)


# 4. KPI Metrics

kpi_query = """
SELECT
    ROUND(SUM(sales), 2) AS total_sales,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity_ordered) AS total_units,
    ROUND(
        SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2
    ) AS average_sales_per_order
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
 AND order_date < CAST(:end_date AS date) + INTERVAL '1 day';
"""

kpi = get_data(kpi_query, params)

total_sales = kpi.loc[0, "total_sales"] or 0
total_orders = kpi.loc[0, "total_orders"] or 0
total_units = kpi.loc[0, "total_units"] or 0
average_order = kpi.loc[0, "average_sales_per_order"] or 0

st.subheader("Bussiness Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    f"${total_sales:,.2f}"
)

col2.metric(
    "Total Orders",
    f"{total_orders:,.0f}"
)

col3.metric(
    "Units Sold",
    f"{total_units:,.0f}"
)

col4.metric(
    "Average Sales / Order",
    f"${average_order:,.2f}"
)

st.divider()


# 5. MONTHLY SALES TREND

monthly_query = """
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    SUM(sales) AS total_sales,
    SUM(quantity_ordered) AS units_sold
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
    AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY sales_month;
"""

monthly_df = get_data(monthly_query, params)

st.subheader("Monthly Sales Trend")

fig_monthly = px.line(
    monthly_df,
    x="sales_month",
    y="total_sales",
    markers=True,
    title="Monthly Revenue Trend",
    labels={
        "sales_month": "Month",
        "total_sales": "Total Sales"
    }
)

fig_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Sales (USD)",
    hovermode="x unified"
)

st.plotly_chart(fig_monthly, use_container_width=True)


# 6. Product Performance

product_query = """
SELECT
    product,
    SUM(quantity_ordered) AS units_sold,
    SUM(sales) AS total_sales
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
    AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY product
ORDER BY total_sales DESC
LIMIT 10;
"""

product_df = get_data(product_query, params)

st.subheader("Top 10 Products by Sales")

fig_product = px.bar(
    product_df.sort_values("total_sales"),
    x="total_sales",
    y="product",
    orientation="h",
    title="Top 10 Products by Revenue",
    labels={
        "total_sales": "Total Sales (USD)",
        "product": "Product"
    }
)

st.plotly_chart(fig_product, use_container_width=True)


# 7. City Performance

city_query = """
SELECT
    city,
    SUM(sales) AS total_sales,
    SUM(quantity_ordered) AS units_sold
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
    AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY city
ORDER BY total_sales DESC;
"""

city_df = get_data(city_query, params)

st.subheader("Sales by City")

fig_city = px.bar(
    city_df,
    x="city",
    y="total_sales",
    title="Revenue by City",
    labels={
        "city": "City",
        "total_sales": "Total Sales (USD)"
    }
)

st.plotly_chart(fig_city, use_container_width=True)


# 8. Hourly Sales

hourly_query = """
SELECT
    EXTRACT(HOUR FROM order_date)::integer AS hour,
    SUM(sales) AS total_sales,
    SUM(quantity_ordered) AS units_sold
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
    AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY EXTRACT(HOUR FROM order_date)
ORDER BY hour;
"""

hourly_df = get_data(hourly_query, params)

st.subheader("Hourly Sales Performance")

fig_hourly = px.bar(
    hourly_df,
    x="hour",
    y="total_sales",
    title="Sales Distribution by Hour",
    labels={
        "hour": "Hour of Day",
        "total_sales": "Total Sales (USD)"
    }
)

fig_hourly.update_xaxes(
    tickmode="linear",
    dtick=1
)

st.plotly_chart(fig_hourly, use_container_width=True)


# 9. Data Detail

with st.expander("View Monthly Sales Data"):
    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True
    )

with st.expander("View Product Performance Data"):
    st.dataframe(
        product_df,
        use_container_width=True,
        hide_index=True
    )

with st.expander("View City Performance Data"):
    st.dataframe(
        city_df,
        use_container_width=True,
        hide_index=True
    )


# 10. Footer

st.divider()

st.caption(
    "Electronics Sales Intelligence | "
    "Data Source: PostgreSQL | "
    "Built with Pythib & Streamlit"
)