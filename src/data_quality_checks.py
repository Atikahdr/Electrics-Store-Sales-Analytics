from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/raw/Electronic_Sales.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset Not Found: {DATA_PATH.resolve()}"
    )

df = pd.read_csv(DATA_PATH)

print("\nELECTRONICS SALES - DATA QUALITY CHECKS")
print("-" * 50)

# 1. Check whether the extra column is a sequential index
if "Unnamed: 0" in df.columns:
    index_col = df["Unnamed: 0"]
    expected_index = pd.Series(range(len(df)))

    print("\n--- EXTRA INDEX COLUMN ---")
    print("Sequential index:", index_col.equals(expected_index))
    print("Unique Values:", index_col.nunique())

# 2. Check invalid numeric values
print("\n--- NUMERIC VALIDATION ---")

for col in ["Quantity Ordered", "Price Each", "Sales"]:
    values = pd.to_numeric(df[col], errors="coerce")

    print(f"\n{col}")
    print("Invalid Numeric:", values.isna().sum())
    print("Zero values:", values.eq(0).sum())
    print("Negative values:", values.lt(0).sum())


# 3. Check date validity
print ("\n--- DATE VALIDATION ---")

dates = pd.to_datetime(df["Order Date"], errors="coerce")

print("Invalid dates:", dates.isna().sum())

valid_dates = dates.dropna()

if not valid_dates.empty:
    print("Earliest order:", valid_dates.min())
    print("Lates order:", valid_dates.max())


# 4. Compare derived month and hour against Order Date
valid_date_mask = dates.notna()

month_mismatch = (
    df.loc[valid_date_mask, "Month"].to_numpy()
    != dates.loc[valid_date_mask].dt.month.to_numpy()
).sum()

hour_mismatch = (
    df.loc[valid_date_mask, "Hour"].to_numpy()
    != dates.loc[valid_date_mask].dt.hour.to_numpy()
).sum()

print("\n--- DATE CONSISTENCY ---")
print("Month mismatches:", month_mismatch)
print("Hour mismatches:", hour_mismatch)


# 5. Check sales calculation
expected_sales = (
    pd.to_numeric(df["Quantity Ordered"], errors="coerce")
    * pd.to_numeric(df["Price Each"], errors="coerce")
)

actual_sales = pd.to_numeric(df["Sales"], errors="coerce")

sales_mismatch = (
    (actual_sales - expected_sales).abs() > 0.01
)

print("\n--- SALES CONSISTENCY ---")
print("Sales calculation mismatch:", sales_mismatch.sum())


# 6. Investigate reated order IDs
print("\n--- ORDER ID CHECK ---")
print("Unique Order IDs:", df["Order ID"].nunique())
print("Rows with repeated Order IDs:",
      df["Order ID"].duplicated(keep=False).sum())


# 7. Inspect product and city categories
print("\n--- CATEGORICAL CHECK ---")

for col in ["Product", "City"]:
    print(f"\n{col}")
    print("Unique values:", df[col].nunique())
    print("Blank strings:", df[col].astype(str).str.strip().eq("").sum())
    print("Leading/trailing whitespace:",
          df[col].ne(df[col].astype(str).str.strip()).sum())

print("\n--- QUALITY CHECK COMPLETED")