import csv
import os
from pathlib import Path

import psycopg

ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR /"data" / "processed" / "electronic_sales_clean.csv"

# PostgresSQL Config
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "electronics_dw",
    "user": "postgres",
    "password": os.environ.get("PGPASSWORD", "",)
}

INSERT_SQL = """
INSERT INTO staging.electronics_sales (
    order_id, product, quantity_ordered, price_each,
    order_date, purchase_address, month, sales, city, hour
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    if not DB_CONFIG["password"]:
        raise ValueError(
            "Password not yet available. Set the PGPASSWORD environment variable"
        )

    columns  =[
        "Order ID", "Product", "Quantity Ordered", "Price Each",
        "Order Date", "Purchase Address", "Month", "Sales", "City", "Hour"
    ]

    inserted = 0

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            # Delete old data to avoid duplicating previous imports.
            # Use only for the staging tables of this project
            cur.execute("TRUNCATE TABLE staging.electronics_sales")

            with CSV_PATH.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                reader = csv.DictReader(file)

                if reader.fieldnames != columns:
                    raise ValueError(
                        f"CSV Header does not match.\n"
                        f"Found: {reader.fieldnames}\n"
                        f"Expected: {columns}"
                    )

                batch = []

                for row in reader:
                    batch.append((
                        row["Order ID"],
                        row["Product"],
                        int(row["Quantity Ordered"]),
                        float(row["Price Each"]),
                        row["Order Date"],
                        row["Purchase Address"],
                        int(row["Month"]),
                        float(row["Sales"]),
                        row["City"],
                        int(row["Hour"]),
                    ))

                    if len(batch) >= 5000:
                        cur.executemany(INSERT_SQL, batch)
                        inserted += len(batch)
                        batch.clear()
                        print(f"Inserted: {inserted:,}")

                if batch:
                    cur.executemany(INSERT_SQL, batch)
                    inserted += len(batch)

            cur.execute(
                "SELECT COUNT(*) FROM staging.electronics_sales"
            )
            total = cur.fetchone()[0]

    print(f"Rows inserted: {inserted:,}")
    print(f"Rows in database: {total:,}")

    if total != inserted:
        raise ValueError("The number of database rows does not match.")

    print("LOAD STATUS: PASSED")

if __name__ == "__main__":
    main()
