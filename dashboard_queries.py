import pandas as pd
from sqlalchemy import text

DATE_FILTER = """
WHERE order_date >= :start_date
  AND order_date < (CAST(:end_date AS date) + INTERVAL '1 day')
"""

def query(engine, sql, start_date, end_date):
    return pd.read_sql(
        text(sql),
        engine,
        params={"start_date": start_date, "end_date": end_date},
    )

def get_kpis(engine, start_date, end_date):
    sql = f"""
    SELECT
        COALESCE(SUM(sales), 0)::numeric AS total_sales,
        COUNT(DISTINCT order_id) AS total_orders,
        COALESCE(SUM(quantity_ordered), 0) AS units_sold,
        COALESCE(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 0)::numeric
            AS avg_sales_per_order
    FROM staging.electronics_sales
    {DATE_FILTER}
    """
    return query(engine, sql, start_date, end_date)

def get_monthly_sales(engine, start_date, end_date):
    sql = f"""
    SELECT DATE_TRUNC('month', order_date)::date AS sales_month,
           SUM(sales)::numeric AS total_sales,
           SUM(quantity_ordered) AS units_sold,
           COUNT(*) AS transaction_lines
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY 1 ORDER BY 1
    """
    return query(engine, sql, start_date, end_date)

def get_top_products(engine, start_date, end_date, limit=10):
    sql = f"""
    SELECT product, SUM(quantity_ordered) AS units_sold,
           COUNT(*) AS transaction_lines, SUM(sales)::numeric AS total_sales
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY product ORDER BY total_sales DESC LIMIT {int(limit)}
    """
    return query(engine, sql, start_date, end_date)

def get_city_performance(engine, start_date, end_date):
    sql = f"""
    SELECT city, SUM(sales)::numeric AS total_sales,
           SUM(quantity_ordered) AS units_sold,
           COUNT(*) AS transaction_lines
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY city ORDER BY total_sales DESC
    """
    return query(engine, sql, start_date, end_date)

def get_hourly_sales(engine, start_date, end_date):
    sql = f"""
    SELECT hour, SUM(sales)::numeric AS total_sales,
           SUM(quantity_ordered) AS units_sold,
           COUNT(*) AS transaction_lines
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY hour ORDER BY hour
    """
    return query(engine, sql, start_date, end_date)

def get_weekly_sales(engine, start_date, end_date):
    sql = f"""
    SELECT DATE_TRUNC('week', order_date)::date AS week_start,
           SUM(sales)::numeric AS total_sales,
           SUM(quantity_ordered) AS units_sold,
           COUNT(*) AS transaction_lines
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY 1 ORDER BY 1
    """
    return query(engine, sql, start_date, end_date)

def get_order_summary(engine, start_date, end_date):
    sql = f"""
    SELECT order_id, MIN(order_date) AS order_date,
           MIN(city) AS city, COUNT(*) AS product_lines,
           COUNT(DISTINCT product) AS distinct_products,
           SUM(quantity_ordered) AS total_units,
           SUM(sales)::numeric AS order_sales
    FROM staging.electronics_sales
    {DATE_FILTER}
    GROUP BY order_id
    ORDER BY order_sales DESC
    LIMIT 500
    """
    return query(engine, sql, start_date, end_date)
