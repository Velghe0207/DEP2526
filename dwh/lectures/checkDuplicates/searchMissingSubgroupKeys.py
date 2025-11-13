import pandas as pd

# ------------------------------------
# CONFIG
# ------------------------------------
MISSING_SUBGROUPS_CSV = "./missing_subgroups.csv"
OUTPUT_UNIQUE = "./missing_unique_subgroups.csv"

# ------------------------------------
# 1. Load missing_subgroups.csv
# ------------------------------------
df = pd.read_csv(MISSING_SUBGROUPS_CSV, dtype=str, delimiter=',')

# Controleren dat de kolom bestaat
if "SubgroupKey" not in df.columns:
    raise ValueError("Kolom 'SubgroupKey' ontbreekt in missing_subgroups.csv")

# ------------------------------------
# 2. Extract unique subgroup keys
# ------------------------------------
unique_missing = df["SubgroupKey"].dropna().astype(str).unique()

# Sorteer voor overzichtelijkheid
unique_missing_sorted = sorted(unique_missing)

# Maak dataframe
output_df = pd.DataFrame({"MissingSubgroupKey": unique_missing_sorted})

# ------------------------------------
# 3. Save to CSV
# ------------------------------------
output_df.to_csv(OUTPUT_UNIQUE, index=False)

# ------------------------------------
# 4. Print resultaten
# ------------------------------------
print("=== RESULTATEN ===")
print(f"Aantal unieke ontbrekende SubgroupKeys: {len(unique_missing_sorted)}")
print(f"CSV aangemaakt: {OUTPUT_UNIQUE}")
