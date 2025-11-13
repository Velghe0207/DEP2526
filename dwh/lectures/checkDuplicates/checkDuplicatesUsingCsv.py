import pandas as pd

# ------------------------------------
# CONFIG
# ------------------------------------
LECTURES_CSV = "../FormattedLectures.csv"
UNIQUE_SUBGROUPS_CSV = "../../../data/cleaned/subgroups/unique_subgroups.csv"

OUTPUT_DUPLICATES = "./duplicates_lectureid_subgroup.csv"
OUTPUT_MISSING_SUBGROUPS = "./missing_subgroups.csv"

# ------------------------------------
# 1. Load formatted lectures CSV
# ------------------------------------
lectures = pd.read_csv(LECTURES_CSV, dtype=str, delimiter=';')

required_cols = ["LectureId", "SubgroupKey"]
for col in required_cols:
    if col not in lectures.columns:
        raise ValueError(f"Kolom '{col}' ontbreekt in {LECTURES_CSV}")

# ------------------------------------
# 2. Load valid subgroup keys from unique_subgroups.csv
# ------------------------------------
valid_df = pd.read_csv(UNIQUE_SUBGROUPS_CSV, dtype=str)

if "SUBGROEPID" not in valid_df.columns:
    raise ValueError("Kolom 'SUBGROEPID' ontbreekt in unique_subgroups.csv")

valid_subgroups = set(valid_df["SUBGROEPID"].astype(str))

# ------------------------------------
# 3. Duplicate detection (LectureId + SubgroupKey)
# ------------------------------------
duplicates = (
    lectures[lectures.duplicated(subset=["LectureId", "SubgroupKey"], keep=False)]
    .sort_values(["LectureId", "SubgroupKey"])
)
duplicates.to_csv(OUTPUT_DUPLICATES, index=False)

# ------------------------------------
# 4. SubgroupKeys not in unique_subgroups.csv
# ------------------------------------
lectures["SubgroupKey"] = lectures["SubgroupKey"].astype(str)
missing_subgroups = lectures[~lectures["SubgroupKey"].isin(valid_subgroups)]

missing_subgroups.to_csv(OUTPUT_MISSING_SUBGROUPS, index=False)

# ------------------------------------
# 5. Print resultaten
# ------------------------------------
print("=== RESULTATEN ===")
print(f"Dubbele LectureId + SubgroupKey combinaties: {len(duplicates)}")
print(f"Rijen met SubgroupKeys die niet in unique_subgroups.csv staan: {len(missing_subgroups)}")

print("\nCSV-bestanden aangemaakt:")
print(f"- {OUTPUT_DUPLICATES}")
print(f"- {OUTPUT_MISSING_SUBGROUPS}")
