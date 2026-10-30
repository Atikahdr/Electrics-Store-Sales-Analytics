from pathlib import Path
import json
import pandas as pd

# CONFIGURATION
#--------------

ROOT_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = ROOT_DIR / "data" / "raw" / "Electronic_Sales.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed"
CLEAN_PATH = OUTPUT_DIR / "electronic_sales_clean.csv"
REPORT_PATH = OUTPUT_DIR / "cleaning_report.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Raw Dataset Not Found: {RAW_PATH}"
        )

    # 1. Load raw data
    df = pd.read_csv(RAW_PATH)
    initial_rows = len(df)

    print("\nELECTRONICS SALES - DATA CLEANING PIPELINE")
    print("-" * 50)
    print(f"Input rows: {initial_rows:,}")
    print(f"Input columns: {len(df.columns)}")

    # 2. Remove the non-business index column
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # 3. Normalize text fields
    text_columns = [
         "Product",
         "Purchase Address",
         "City",
     ]

    for col in text_columns:
        if col not in df.columns:
            raise ValueError(f"Required column not found: {col}")

        df[col] = df[col].astype("string").str.strip()

        if df[col].isna().any() or df[col].eq("").any():
            raise ValueError(
                F"Column {col} has empty values after cleaning. "
            )

    # Convert data types
    required_columns = [
        "Order ID",
        "Product",
        "Quantity Ordered",
        "Price Each",
        "Order Date",
        "Purchase Address",
        "Month",
        "Sales",
        "City",
        "Hour"
    ]

    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Required column not found: {sorted(missing_columns)}"
        )

    for col in [
        "Order ID",
        "Quantity Ordered",
        "Month",
        "Hour"
    ]:
        df[col] = pd.to_numeric(df[col], errors="raise")

        if df[col].isna().any():
            raise ValueError(f"{col} has a null value.")

        if (df[col] % 1 !=0).any():
            raise ValueError(f"{col} must contain an integer.")

        df[col] = df[col].astype("int64")

    for col in ["Price Each", "Sales"]:
        df[col] = pd.to_numeric(df[col], errors="raise")

        if df[col].isna().any():
            raise ValueError(f"{col} has a null value.")

        if not df[col].map(
            lambda value: pd.notna(value) and abs(value) != float("inf")
        ).all():
            raise ValueError(f"{col} contains a non-finite value.")

    df["Order Date"] = pd.to_datetime(
        df["Order Date"],
        errors="raise",
    )

    # 5. Busines-rule validation
    if (df["Quantity Ordered"] <= 0).any():
        raise ValueError("The quantity must be positive.")

    if (df["Price Each"] <= 0).any():
        raise ValueError("Price Each must be positive.")

    if not df["Month"].between(1, 12).all():
        raise ValueError("The month must be in range of 1-12.")

    if not df["Hour"].between(0, 23).all():
        raise ValueError("The hour must be in range 0-23.")

    # 6. Validate derived columns against Order Date
    expected_month = df["Order Date"].dt.month
    expected_hour = df["Order Date"].dt.hour

    month_mismatches = int(
        df["Month"].ne(expected_month).sum()
    )
    hour_mismatches = int(
        df["Hour"].ne(expected_hour).sum()
    )

    if month_mismatches:
        raise ValueError(
            f"Inconsistent month: {month_mismatches} rows"
        )

    if hour_mismatches:
        raise ValueError(
            f"Inconsistent hour: {hour_mismatches} rows)"
        )

    # Derive these values from the canonical timestamp
    df["Month"] = expected_month.astype("int64")
    df["Hour"] = expected_hour.astype("int64")

    # 7. Validate Sales = Quantity * Price
    expected_sales = (
        df["Quantity Ordered"] * df["Price Each"]
    ).round(2)

    sales_mismatches = int(
        (df["Sales"].round(2) - expected_sales).abs().gt(0.01).sum()
    )

    if sales_mismatches:
        raise ValueError(
            f"Inconsistant Sales: {sales_mismatches} rows."
        )

    # Standardize Sales to two decimal places
    df["Sales"] = expected_sales

    # 8. Do not delete repeated Order IDs or rowa automatically
    duplicate_mask = df.duplicated(keep="first")
    duplicate_rows_excess = int(duplicate_mask.sum())

    duplicate_groups = int(
        df.loc[df.duplicated(keep=False)]
        .drop_duplicates()
        .shape[0]
    )

    # Save duplicate records before removing theme
    if duplicate_rows_excess > 0:
        duplicate_audit = df.loc[duplicate_mask].copy()

        # Include the original CSV line number for tracebility
        # CSV line 1 contains the header.
        duplicate_audit.insert(
            0,
            "source_csv_line",
            duplicate_audit.index + 2
        )

        audit_path = OUTPUT_DIR / "duplicate_rows_removed.csv"
        duplicate_audit.to_csv(audit_path, index=False)

        print(f"Duplicate audit saved: {audit_path}")

    # Remove duplicate records, retaining the first occurrence
    df = df.loc[~duplicate_mask].copy()

    # Validate the result
    remaining_duplicates = int(df.duplicated().sum())

    if remaining_duplicates:
        raise ValueError(
            f"{remaining_duplicates} duplicates were still found"
            "after the deduplication process"
        )

    print("\n--- DEDUPLICATION SUMMARY ---")
    print(f"Duplicate groups: {duplicate_groups:,}")
    print(f"Excess rows removed: {duplicate_rows_excess:,}")
    print(f"Rows remaining: {len(df):,}")
    print(f"Remaining full duplicates: {remaining_duplicates:,}")

    # 9 . Validate date range; January 2020 is retained
    min_date = df["Order Date"].min()
    max_date = df["Order Date"].max()

    january_2020_rows = int(
        df["Order Date"].dt.to_period("M").eq("2020-01").sum()
    )

    # 10. Save cleaned data
    df.to_csv(CLEAN_PATH, index=False)

    # 11. Save an audit report
    report = {
        "input_file": RAW_PATH.name,
        "output_file": CLEAN_PATH.name,
        "rows_input": initial_rows,
        "rows_output": len(df),
        "rows_removed": initial_rows - len(df),
        "columns_input": 11,
        "columns_output": len(df.columns),
        "removed_columns": ["Unnamed: 0"],
        "duplicate_group_detected": duplicate_groups,
        "duplicate_excess_row_removed": duplicate_rows_excess,
        "missing_values_after_cleaning": int(
            df.isna().sum().sum()
        ),  
        "month_mismatch": month_mismatches,
        "hour_mismatch": hour_mismatches,
        "sales_mismatch": sales_mismatches,
        "january_2020_row_retained": january_2020_rows,
        "minimum_order_date": min_date.isoformat(),
        "maxmium_order_date": max_date.isoformat(),
        "deduplication_assumption": (
            "Fully identical business records are treated as "
            "duplicate entries; one row per group is retained."
        ),
        "status": "PASSED"
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    # 12. Print final summary
    print("\n--- CLEANING SUMMARY ---")
    print(f"Rows input: {initial_rows:,}")
    print(f"Rows output: {len(df):,}")
    print(f"Rows removed: {initial_rows - len(df):,}")
    print(f"Columns input: 11")
    print(f"Columns output: {len(df.columns)}")
    print(f"Duplicate groups detected: {duplicate_groups:,}")
    print(f"Duplicate rows removed: {duplicate_rows_excess:,}")
    print(f"Full duplicates remaining: {df.duplicated().sum():,}")
    print(f"Missing Values: {df.isna().sum().sum():,}")
    print(f"January 2020 rows retained: {january_2020_rows}")
    print(f"Date range: {min_date} to {max_date}")
    print(f"Cleaned data: {CLEAN_PATH}")
    print(f"Audit report: {REPORT_PATH}")
    print("\nPIPELINE STATUS: PASSED")

 
if __name__ == "__main__":
    main()