import csv
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyodbc


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"D:\Documents2\School\26-EP3\DEP\repo"
    r"\DEP2-2025-2026-groep12\00 data"
)

INPUT_DIR = BASE_DIR / "raw" / "lecture reservations"

# Optioneel tussentijds bestand met alle samengevoegde lectures
MERGED_CSV = BASE_DIR / "raw" / "lectures" / "AllLectures.csv"

# Definitieve outputs
OUTPUT_CSV = BASE_DIR / "raw" / "lectures" / "FormattedLectures.csv"

MISSING_KEYS_CSV = (
    BASE_DIR
    / "left out"
    / "FormattedLectures_missingRoomOrClass.csv"
)

SERVER = r"localhost\MSSQLSERVER2019"
DATABASE = "DEP2"
DRIVER = "ODBC Driver 17 for SQL Server"

# Zet op False wanneer je AllLectures.csv niet meer apart wilt bewaren
SAVE_MERGED_CSV = True


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def read_csv_file(file_path: Path) -> pd.DataFrame:
    """
    Leest een CSV-bestand in.

    Eerst wordt geprobeerd met puntkomma als separator, omdat TimeEdit
    doorgaans puntkomma's gebruikt. Wanneer het resultaat slechts één
    kolom bevat, wordt ook een komma geprobeerd.
    """
    try:
        df = pd.read_csv(
            file_path,
            sep=";",
            quoting=csv.QUOTE_NONE,
            on_bad_lines="skip",
            engine="python",
            dtype=str,
        )

        # Mogelijk is het toch een komma-gescheiden bestand
        if len(df.columns) == 1:
            comma_df = pd.read_csv(
                file_path,
                sep=",",
                on_bad_lines="skip",
                engine="python",
                dtype=str,
            )

            if len(comma_df.columns) > 1:
                df = comma_df

        return df

    except Exception as error:
        raise RuntimeError(
            f"Kon bestand niet inlezen: {file_path.name}"
        ) from error


def read_all_csv_from_directory(directory: Path) -> list[pd.DataFrame]:
    """Leest alle CSV-bestanden uit een directory."""
    if not directory.exists():
        raise FileNotFoundError(
            f"De inputmap bestaat niet:\n{directory}"
        )

    csv_files = sorted(directory.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"Geen CSV-bestanden gevonden in:\n{directory}"
        )

    dataframes = []

    print(f"CSV-bestanden zoeken in:\n{directory}\n")

    for file_path in csv_files:
        try:
            df = read_csv_file(file_path)
            dataframes.append(df)

            print(
                f"✅ Geladen: {file_path.name} "
                f"({len(df):,} rijen, {len(df.columns)} kolommen)"
            )

        except Exception as error:
            print(f"⚠️ Overgeslagen: {file_path.name}")
            print(f"   Reden: {error}")

    return dataframes


def parse_datetime_column(series: pd.Series) -> pd.Series:
    """
    Parseert datums uit TimeEdit.

    Het vaste formaat wordt eerst geprobeerd. Wanneer sommige waarden
    daarvan afwijken, gebruikt pandas voor die waarden een flexibelere
    parsing.
    """
    parsed = pd.to_datetime(
        series,
        format="%m/%d/%Y %H:%M:%S",
        errors="coerce",
    )

    missing_mask = parsed.isna() & series.notna()

    if missing_mask.any():
        parsed.loc[missing_mask] = pd.to_datetime(
            series.loc[missing_mask],
            errors="coerce",
        )

    return parsed


def split_subgroups(value) -> list:
    """Splitst pipe-separated subgroepen naar afzonderlijke waarden."""
    if pd.isna(value):
        return [None]

    value = str(value).strip()

    if not value:
        return [None]

    return [
        subgroup.strip()
        for subgroup in value.split("|")
        if subgroup.strip()
    ] or [None]


def find_activity_key(row, activity_lookup, default_activity_key):
    """
    Zoekt de ActivityKey op basis van de eerste ingevulde activitykolom.
    """
    activity_columns = [
        "WorkFormCourse",
        "WorkFormExam",
        "WorkFormEvaluation",
        "EducationActivity",
        "LearningEnvironment",
        "ExamEnvironment",
    ]

    for column in activity_columns:
        value = row.get(column)

        if pd.notna(value) and str(value).strip():
            lookup_key = (column, str(value).strip())

            if lookup_key in activity_lookup:
                return activity_lookup[lookup_key]

    return default_activity_key


# ============================================================
# 3. MERGE ALL INDIVIDUAL CSV FILES
# ============================================================

print(f"Huidige werkmap: {os.getcwd()}\n")

all_dataframes = read_all_csv_from_directory(INPUT_DIR)

if not all_dataframes:
    raise RuntimeError(
        "Geen bruikbare CSV-bestanden konden worden ingelezen."
    )

merged_df = pd.concat(
    all_dataframes,
    ignore_index=True,
    sort=False,
)

print("\n" + "=" * 60)
print("MERGE SUMMARY")
print("=" * 60)
print(f"Aantal samengevoegde bestanden: {len(all_dataframes):,}")
print(f"Aantal samengevoegde rijen:     {len(merged_df):,}")
print(f"Aantal kolommen:                 {len(merged_df.columns):,}")

# Maak outputmappen aan indien nodig
MERGED_CSV.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
MISSING_KEYS_CSV.parent.mkdir(parents=True, exist_ok=True)

if SAVE_MERGED_CSV:
    merged_df.to_csv(
        MERGED_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"💾 Samengevoegd bestand opgeslagen:\n{MERGED_CSV}")


# ============================================================
# 4. PREPARE AND CLEAN MERGED DATA
# ============================================================

df = merged_df.copy()

required_columns = [
    "Id",
    "Start",
    "End",
    "OlodPointers",
    "Rooms",
    "Classgroups",
]

missing_required_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_required_columns:
    raise KeyError(
        "De volgende verplichte kolommen ontbreken:\n"
        + "\n".join(f"- {column}" for column in missing_required_columns)
    )

drop_columns = [
    "Updated",
    "UpdatedBy",
    "Status",
    "ReasonTeacher",
    "ReasonRoom",
    "InternExtern",
    "Department",
    "User",
    "CoordinationService",
    "ContactPerson",
    "MobileEquipment",
    "GroupHogent",
    "Person",
    "Student",
    "Invigilator",
]

# errors='ignore' voorkomt een fout wanneer een kolom niet bestaat
df = df.drop(columns=drop_columns, errors="ignore")

df = df.rename(columns={"Id": "LectureId"})

# Normaliseer belangrijke tekstkolommen
df["LectureId"] = df["LectureId"].astype("string").str.strip()
df["OlodPointers"] = df["OlodPointers"].astype("string").str.strip()
df["Rooms"] = df["Rooms"].astype("string").str.strip()
df["Classgroups"] = df["Classgroups"].astype("string").str.strip()


# ============================================================
# 5. CREATE DATE AND TIME KEYS
# ============================================================

df["ParsedStart"] = parse_datetime_column(df["Start"])
df["ParsedEnd"] = parse_datetime_column(df["End"])

invalid_datetime_mask = (
    df["ParsedStart"].isna()
    | df["ParsedEnd"].isna()
)

print("\n" + "=" * 60)
print("DATE PARSING")
print("=" * 60)
print(
    f"Rijen met ongeldige Start- of End-datum: "
    f"{invalid_datetime_mask.sum():,}"
)

df["DateKey"] = (
    df["ParsedStart"]
    .dt.strftime("%Y%m%d")
    .astype("Int64")
)

df["FromTimeKey"] = (
    df["ParsedStart"]
    .dt.strftime("%H%M%S")
    .astype("Int64")
)

df["UntilTimeKey"] = (
    df["ParsedEnd"]
    .dt.strftime("%H%M%S")
    .astype("Int64")
)

# Specifieke correctie
df.loc[
    df["LectureId"] == "479883",
    "OlodPointers",
] = "193745"


# ============================================================
# 6. SPLIT SUBGROUPS INTO MULTIPLE ROWS
# ============================================================

rows_before_explode = len(df)

df["SubgroupKey"] = df["Classgroups"].apply(split_subgroups)
df = df.explode("SubgroupKey", ignore_index=True)
df = df.drop(columns=["Classgroups"])

print("\n" + "=" * 60)
print("SUBGROUP SPLITTING")
print("=" * 60)
print(f"Rijen vóór het splitsen: {rows_before_explode:,}")
print(f"Rijen na het splitsen:   {len(df):,}")
print(
    f"Extra rijen door meerdere subgroepen: "
    f"{len(df) - rows_before_explode:,}"
)


# ============================================================
# 7. LOAD FOREIGN KEY MAPPINGS FROM SQL SERVER
# ============================================================

connection_string = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=Yes;"
    "TrustServerCertificate=Yes;"
)

print("\n" + "=" * 60)
print("DATABASE LOOKUPS")
print("=" * 60)
print(f"Verbinden met database {DATABASE} op {SERVER}...")

with pyodbc.connect(connection_string) as connection:
    class_map = pd.read_sql(
        """
        SELECT
            ClassCode,
            ClassKey
        FROM dbo.DimClass
        """,
        connection,
    )

    room_map = pd.read_sql(
        """
        SELECT
            Code AS RoomCode,
            RoomKey
        FROM dbo.DimRoom
        """,
        connection,
    )

    activity_map = pd.read_sql(
        """
        SELECT
            ActivityKey,
            SourceColumn,
            SourceValue
        FROM dbo.DimActivity
        """,
        connection,
    )

print(f"Class mappings geladen:    {len(class_map):,}")
print(f"Room mappings geladen:     {len(room_map):,}")
print(f"Activity mappings geladen: {len(activity_map):,}")


# ============================================================
# 8. MERGE CLASSKEY
# ============================================================

# Neem bij meerdere OlodPointers voorlopig de eerste waarde
df["FirstOlodPointer"] = (
    df["OlodPointers"]
    .str.split("|", regex=False)
    .str[0]
    .str.strip()
)

df["FirstOlodPointer"] = pd.to_numeric(
    df["FirstOlodPointer"],
    errors="coerce",
).astype("Int64")

class_map["ClassCode"] = pd.to_numeric(
    class_map["ClassCode"],
    errors="coerce",
).astype("Int64")

class_map["ClassKey"] = pd.to_numeric(
    class_map["ClassKey"],
    errors="coerce",
).astype("Int64")

# Bescherming tegen onverwachte duplicaten in DimClass
duplicate_class_codes = class_map["ClassCode"].duplicated(
    keep=False
).sum()

if duplicate_class_codes:
    print(
        f"⚠️ DimClass bevat {duplicate_class_codes:,} rijen met "
        "dubbele ClassCode-waarden."
    )

    class_map = class_map.drop_duplicates(
        subset=["ClassCode"],
        keep="first",
    )

df = df.merge(
    class_map,
    how="left",
    left_on="FirstOlodPointer",
    right_on="ClassCode",
    validate="many_to_one",
)

df = df.drop(
    columns=["ClassCode", "FirstOlodPointer"],
    errors="ignore",
)


# ============================================================
# 9. MERGE ROOMKEY
# ============================================================

# Neem bij meerdere lokalen voorlopig het eerste lokaal
df["FirstRoom"] = (
    df["Rooms"]
    .str.split("|", regex=False)
    .str[0]
    .str.strip()
)

room_map["RoomCode"] = (
    room_map["RoomCode"]
    .astype("string")
    .str.strip()
)

room_map["RoomKey"] = pd.to_numeric(
    room_map["RoomKey"],
    errors="coerce",
).astype("Int64")

duplicate_room_codes = room_map["RoomCode"].duplicated(
    keep=False
).sum()

if duplicate_room_codes:
    print(
        f"⚠️ DimRoom bevat {duplicate_room_codes:,} rijen met "
        "dubbele RoomCode-waarden."
    )

    room_map = room_map.drop_duplicates(
        subset=["RoomCode"],
        keep="first",
    )

df = df.merge(
    room_map,
    how="left",
    left_on="FirstRoom",
    right_on="RoomCode",
    validate="many_to_one",
)

df = df.drop(
    columns=["RoomCode", "FirstRoom"],
    errors="ignore",
)


# ============================================================
# 10. DETERMINE ACTIVITYKEY
# ============================================================

activity_map["SourceColumn"] = (
    activity_map["SourceColumn"]
    .fillna("")
    .astype(str)
    .str.strip()
)

activity_map["SourceValue"] = (
    activity_map["SourceValue"]
    .fillna("")
    .astype(str)
    .str.strip()
)

activity_lookup = {
    (row.SourceColumn, row.SourceValue): row.ActivityKey
    for row in activity_map.itertuples(index=False)
    if row.SourceValue
}

default_activity_rows = activity_map[
    activity_map["SourceValue"] == ""
]

default_activity_key = (
    default_activity_rows["ActivityKey"].iloc[0]
    if not default_activity_rows.empty
    else None
)

df["ActivityKey"] = df.apply(
    find_activity_key,
    axis=1,
    args=(activity_lookup, default_activity_key),
)

df["ActivityKey"] = pd.to_numeric(
    df["ActivityKey"],
    errors="coerce",
).astype("Int64")


# ============================================================
# 11. ADD EMPTY ATTENDANCE COLUMNS
# ============================================================

df["UserCount"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
df["TotalStudents"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
df["AttendanceRate"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Float64",
)

final_columns = [
    "LectureId",
    "DateKey",
    "FromTimeKey",
    "UntilTimeKey",
    "ClassKey",
    "SubgroupKey",
    "RoomKey",
    "ActivityKey",
    "UserCount",
    "TotalStudents",
    "AttendanceRate",
]

df_final = df[final_columns].copy()

df_final["ClassKey"] = pd.to_numeric(
    df_final["ClassKey"],
    errors="coerce",
).astype("Int64")

df_final["RoomKey"] = pd.to_numeric(
    df_final["RoomKey"],
    errors="coerce",
).astype("Int64")

df_final["SubgroupKey"] = (
    df_final["SubgroupKey"]
    .astype("string")
    .str.strip()
)


# ============================================================
# 12. REMOVE EXACT DUPLICATES
# ============================================================

rows_before_deduplication = len(df_final)

df_final = df_final.drop_duplicates().reset_index(drop=True)

duplicates_removed = rows_before_deduplication - len(df_final)

print("\n" + "=" * 60)
print("DUPLICATE CHECK")
print("=" * 60)
print(f"Exacte dubbele rijen verwijderd: {duplicates_removed:,}")


# ============================================================
# 13. SPLIT VALID AND INVALID ROWS
# ============================================================

invalid_mask = (
    df_final["RoomKey"].isna()
    | df_final["ClassKey"].isna()
)

invalid_df = df_final.loc[invalid_mask].copy()
valid_df = df_final.loc[~invalid_mask].copy()

valid_df.to_csv(
    OUTPUT_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

invalid_df.to_csv(
    MISSING_KEYS_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 14. PRINT SUMMARY
# ============================================================

missing_class_keys = df_final["ClassKey"].isna().sum()
missing_room_keys = df_final["RoomKey"].isna().sum()
missing_activity_keys = df_final["ActivityKey"].isna().sum()

missing_both = (
    df_final["ClassKey"].isna()
    & df_final["RoomKey"].isna()
).sum()

print("\n" + "=" * 60)
print("FORMATTING COMPLETE")
print("=" * 60)

print(f"Totale rijen verwerkt: {len(df_final):,}")
print(f"Geldige rijen:          {len(valid_df):,}")
print(f"Ongeldige rijen:        {len(invalid_df):,}")

print("\nMissing key breakdown:")
print(f"  - Missing ClassKeys:    {missing_class_keys:,}")
print(f"  - Missing RoomKeys:     {missing_room_keys:,}")
print(f"  - Missing beide keys:   {missing_both:,}")
print(f"  - Missing ActivityKeys: {missing_activity_keys:,}")

print("\nOutputbestanden:")
print(f"✅ Geldige lectures:\n   {OUTPUT_CSV}")
print(f"⚠️ Lectures met ontbrekende keys:\n   {MISSING_KEYS_CSV}")

if SAVE_MERGED_CSV:
    print(f"📦 Samengevoegde brondata:\n   {MERGED_CSV}")