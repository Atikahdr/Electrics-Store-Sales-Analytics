from db1 import get_data

views = [
    "product_performance",
    "monthly_sales",
    "city_performance",
    "hourly_sales"
]

for view in views:
    print(f"\nTesting: {view}")

    query = f"""
        SELECT *
        FROM analytics.{view}
        LIMIT 5
    """

    df = get_data(query)

    print(df.head())
    print("Rows returned:", len(df))

    