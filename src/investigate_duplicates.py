from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT_DIR / "data" / "raw" / "Electronic_Sales.csv"
OUTPUT_DIR = ROOT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW_PATH)

print("\nDUPLICATE INVESTIGATION")
print("-" * 50)

# Preserve original data for comparison
original =df.copy()

# Apply the same normalization as the cleaning pipeline
normalized = df.drop(
    columns=["Unnamed: 0"],
    errors="ignore",
).copy()

for col in ["Product", "Purchase Address", "City"]:
    normalized[col] = normalized[col].astype("string").str.strip()

# Identify duplicate groups after normalization
duplicate_mask = normalized.duplicated(keep=False)
duplicate_rows = normalized.loc[duplicate_mask].copy()

print("Raw rows:", len(original))
print("Rows involved in duplicate groups:", len(duplicate_rows))
print(
    "Duplicate excess rows:",
    int(normalized.duplicated(keep="first").sum()),
)
print(
    "Number of duplicate groups:",
    int(
        normalized.loc[duplicate_mask]
        .drop_duplicates()
        .shape[0]
    ),
)

# Save all flagged rows with their original source index
source_index = original.loc[duplicate_mask, ["Unnamed: 0"]].copy()
source_index.columns = ["source_unnamed_index"]

audit = pd.concat(
    [
        source_index.reset_index(drop=True),
        duplicate_rows.reset_index(drop=True),
    ],
    axis=1,
)

audit_path = OUTPUT_DIR / "duplicate_investigation.csv"
audit.to_csv(audit_path, index=False)

print("\n--- FIRST 20 FLAGGED ROWS ----")
print(audit.head(20).to_string(index=False))

print("\n--- DUPLICATE GROUP SIZES ---")
group_sizes = (
    duplicate_rows.groupby(
        list(normalized.columns),
        dropna=False,
    )
    .size()
    .sort_values(ascending=False)
)

print(group_sizes.head(20).to_string())

print("\nAudit file save to:", audit_path)
print("Original dataset was not modified.")