import pandas as pd
import pyodbc

# ------------------------------------
# CONFIG
# ------------------------------------
LECTURES_CSV = "../FormattedLectures.csv"

OUTPUT_DUPLICATES = "./duplicates_lectureid_subgroup.csv"
OUTPUT_MISSING_SUBGROUPS = "./missing_subgroups.csv"

# ------------------------------------
# DATABASE CONNECTIE
# ------------------------------------
server = "127.0.0.1,1500"
database = "DEP2"
username = "sa"
password = "dep2025-G12"
driver = "ODBC Driver 17 for SQL Server"

conn = pyodbc.connect(
    f"Driver={{{driver}}};"
    f"Server={server};"
    f"Database={database};"
    f"UID={username};"
    f"PWD={password};"
)

# ------------------------------------
# 1. Load formatted lectures CSV
# ------------------------------------
lectures = pd.read_csv(LECTURES_CSV, dtype=str, delimiter=';')

# Controleren dat de vereiste kolommen bestaan
required_cols = ["LectureId", "SubgroupKey"]
for col in required_cols:
    if col not in lectures.columns:
        raise ValueError(f"Kolom '{col}' ontbreekt in CSV {LECTURES_CSV}")

# ------------------------------------
# 2. Load DimSubgroup from database
# ------------------------------------
query = "SELECT SubgroupKey FROM dbo.DimSubgroup"
dim_subgroups = pd.read_sql_query(query, conn)

dim_subgroups["SubgroupKey"] = dim_subgroups["SubgroupKey"].astype(str)
valid_subgroups = set(dim_subgroups["SubgroupKey"])

# ------------------------------------
# 3. Duplicate detection
# ------------------------------------
duplicates = (
    lectures[lectures.duplicated(subset=["LectureId", "SubgroupKey"], keep=False)]
    .sort_values(["LectureId", "SubgroupKey"])
)
duplicates.to_csv(OUTPUT_DUPLICATES, index=False)

# ------------------------------------
# 4. Missing subgroup keys
# ------------------------------------
lectures["SubgroupKey"] = lectures["SubgroupKey"].astype(str)
missing_subgroups = lectures[~lectures["SubgroupKey"].isin(valid_subgroups)]
missing_subgroups.to_csv(OUTPUT_MISSING_SUBGROUPS, index=False)

# ------------------------------------
# 5. Print resultaten
# ------------------------------------
print("=== RESULTATEN ===")
print(f"Dubbele LectureId + SubgroupKey combinaties: {len(duplicates)}")
print(f"Rijen met SubgroupKeys die niet bestaan in DimSubgroup: {len(missing_subgroups)}")

print("\nCSV-bestanden aangemaakt:")
print(f"- {OUTPUT_DUPLICATES}")
print(f"- {OUTPUT_MISSING_SUBGROUPS}")
