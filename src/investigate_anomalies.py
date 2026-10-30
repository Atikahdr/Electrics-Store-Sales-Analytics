from pathlib import Path
import pandas as pd

path = Path("data/raw/Electronic_Sales.csv")
df = pd.read_csv(path)

print("\n INVESTIGATION: ELECTRONICS SALES")
print("-" * 50)

# 1. Investigate Unnamed: 0
print("\n--- UNNAMED INDEX ---")
if "Unnamed: 0" in df.columns:
    col = df["Unnamed: 0"]
    print("Data Type:", col.dtype)
    print("Unique Values:", col.nunique())
    print("Minimum:", col.min())
    print("Maximum:", col.max())
    print("First 20 values:", col.head(20).tolist())
    print("Most frequent values:")
    print(col.value_counts().head(10).to_string())

# 2. Inspect City whitespace
print("\n--- CITY WHITESPACE ---")
city = df["City"].astype("string")
trimmed = city.str.strip()

print("Rows Changed by strip:", int(city.ne(trimmed).sum()))
print("Original examples:")
for value in city.drop_duplicates().head(15):
    print(repr(value))
 
print("\nUnique cities before strip:", city.nunique())
print("Unique cities after strip:", trimmed.nunique())

# 3. Inspect repeated Order IDs
print("\n--- REPEATED ORDER IDs")
counts = df["Order ID"].value_counts()
repeated_ids = counts[counts > 1]

print("Unique Order IDs:", df["Order ID"].nunique())
print("IDs appearing more than once:", len(repeated_ids))
print(" ", int(counts[counts > 1].sum()))

if not repeated_ids.empty:
    example_id = repeated_ids.index[0]
    print(f"\nExample Order ID: {example_id}")
    print(
        df.loc[df["Order ID"] == example_id].to_string(index=False)
    )

# 4. Inspect date boundaries and months
print("\n--- DATE RANGE ---")
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="raise")

print("Minimum date:", df["Order Date"].min())
print("Maximum date:", df["Order Date"].max())
print("\nRows per month:")
print(df["Order Date"].dt.to_period("M").value_counts().sort_index())

# 5. Investigate Unnamed: 0 by month
print("\n--- INDEX PATTERN BY MONTH ---")

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="raise")
df["Month_Period"] = df["Order Date"].dt.to_period("M")

if "Unnamed: 0" in df.columns:
    print("\nIndex examples by month:")
    for month, group in df.groupby("Month_Period", sort=True):
        print(
            f"{month}:"
            f"first={group['Unnamed: 0'].head(3).tolist()}, "
            f"unique_index={group['Unnamed: 0'].nunique()}"
        )

# 6. Inspect January 2020 records
print("\n--- JANUARY 2020 RECORDS ---")

jan_2020 = df[df["Order Date"].dt.to_period("M") == "2020-01"]

print("Rows:", len(jan_2020))

if not jan_2020.empty:
    print(
        jan_2020[
            [
                "Order ID",
                "Product",
                "Quantity Ordered",
                "Price Each",
                "Order Date",
                "Sales",
                "City",
                "Hour"
            ]
        ].to_string(index=False)
    )

    print("\nJanuary 2020 product counts:")
    print(jan_2020["Product"].value_counts().to_string())

    print("\nJanuary 2020 date distribution:")
    print(
        jan_2020["Order Date"]
        .dt.strftime("%Y-%m-%d")
        .value_counts()
        .sort_index()
        .to_string()
    )

print("\n--- INVESTIGATION COMPLETED")