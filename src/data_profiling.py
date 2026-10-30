from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/raw/Electronic_Sales.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH.resolve()}")

df = pd.read_csv(DATA_PATH)

print("ELECTRONICS SALES - DATA PROFILING")
print("-" * 50)

print(f"\nNumber of Rows: {df.shape[0]:,}")
print(f"Number of Columns: {df.shape[1]:,}")

print("\n--- Data Type ---")
print(df.dtypes.to_string())

print("\n--- Missing Values ---")
missing = df.isnull().sum()
missing_report = pd.DataFrame({
    "missing_count": missing,
    "missing_percent": (missing / len(df) * 100).round(2)
})
print(missing_report.to_string())

print("\n--- Duplicate ---")
print(f"Full duplicate rows: {df.duplicated().sum():,}")

print("\n--- Sample Data ---")
print(df.head().to_string(index=False))