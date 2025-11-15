import pandas as pd
import pyodbc
from pathlib import Path

# ---------------- Config ----------------
CSV_PATH = Path(r"dwh\lectures\FormattedLectures.csv")

server = "127.0.0.1,1500"
database = "DEP2"
username = "sa"
password = "dep2025-G12"
driver = "ODBC Driver 17 for SQL Server"

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=Yes;"
)

# --------------- Read & tidy CSV ---------------
df = pd.read_csv(
    CSV_PATH,
    sep=';',
    na_values=["NULL", "", "nan"],
    keep_default_na=True,
    dtype=str
)

expected_cols = [
    "LectureId","DateKey","FromTimeKey","UntilTimeKey",
    "ClassKey","SubgroupKey","RoomKey","ActivityKey",
    "UserCount","TotalStudents","AttendanceRate"
]

missing = [c for c in expected_cols if c not in df.columns]
if missing:
    raise ValueError(f"CSV missing columns: {missing}")

df = df[expected_cols].copy()

# Replace blanks with NaN
df = df.replace(r'^\s*$', pd.NA, regex=True)

# Convert numeric columns
int_cols = ["LectureId","DateKey","FromTimeKey","UntilTimeKey",
            "ClassKey","SubgroupKey","RoomKey","ActivityKey",
            "UserCount","TotalStudents"]

for col in int_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').astype("Int64")

# Drop rows missing required fields
df = df.dropna(subset=["LectureId", "SubgroupKey", "DateKey", "FromTimeKey", "UntilTimeKey"])

# ============================================================
# 🔍 Remove duplicate LectureId + SubgroupKey combinations
# ============================================================
before_count = len(df)
df = df.drop_duplicates(subset=["LectureId", "SubgroupKey"], keep="last")
after_count = len(df)
duplicates_removed = before_count - after_count

if duplicates_removed > 0:
    print(f"⚠️ Skipped {duplicates_removed} duplicate rows (same LectureId + SubgroupKey).")

# ============================================================
# 🔍 Filter out rows with SubgroupKeys not existing in DimSubgroup
# ============================================================
print("🔗 Checking which SubgroupKeys exist in dbo.DimSubgroup...")

with pyodbc.connect(conn_str) as conn:
    existing_subgroups = pd.read_sql("SELECT SubgroupKey FROM dbo.DimSubgroup", conn)
existing_keys = set(existing_subgroups['SubgroupKey'].astype(int).tolist())

before_filter = len(df)
df = df[df['SubgroupKey'].isin(existing_keys)]
after_filter = len(df)
skipped_subgroups = before_filter - after_filter

print(f"⚠️ Skipped {skipped_subgroups} rows with non-existing SubgroupKeys.")

# Convert pandas NA → Python None for pyodbc
records = []
for _, r in df.iterrows():
    records.append((
        None if pd.isna(r["LectureId"])     else int(r["LectureId"]),
        None if pd.isna(r["DateKey"])       else int(r["DateKey"]),
        None if pd.isna(r["FromTimeKey"])   else int(r["FromTimeKey"]),
        None if pd.isna(r["UntilTimeKey"])  else int(r["UntilTimeKey"]),
        None if pd.isna(r["ClassKey"])      else int(r["ClassKey"]),
        None if pd.isna(r["SubgroupKey"])   else int(r["SubgroupKey"]),
        None if pd.isna(r["RoomKey"])       else int(r["RoomKey"]),
        None if pd.isna(r["ActivityKey"])   else int(r["ActivityKey"]),
        None if pd.isna(r["UserCount"])     else int(r["UserCount"]),
        None if pd.isna(r["TotalStudents"]) else int(r["TotalStudents"]),
    ))

print(f"Filtered dataset: {len(records)} valid FactLecture rows ready for upload.")

# ---------------- SQL ----------------
CREATE_TABLE_SQL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'FactLecture' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.FactLecture (
        LectureID     INT          NOT NULL,
        DateKey       INT          NOT NULL FOREIGN KEY REFERENCES dbo.DimDate(DateKey),
        FromTimeKey   INT          NOT NULL FOREIGN KEY REFERENCES dbo.DimTime(TimeKey),
        UntilTimeKey  INT          NOT NULL FOREIGN KEY REFERENCES dbo.DimTime(TimeKey),
        ClassKey      INT          NULL FOREIGN KEY REFERENCES dbo.DimClass(ClassKey),
        SubgroupKey   INT          NOT NULL FOREIGN KEY REFERENCES dbo.DimSubgroup(SubgroupKey),
        RoomKey       INT          NULL FOREIGN KEY REFERENCES dbo.DimRoom(RoomKey),
        ActivityKey   INT          NULL FOREIGN KEY REFERENCES dbo.DimActivity(ActivityKey),
        UserCount     INT          NULL,
        TotalStudents INT          NULL,
        AttendanceRate AS (CASE WHEN TotalStudents = 0 THEN 0
                                ELSE CAST(UserCount AS float) / TotalStudents END),
        CONSTRAINT PK_FactLecture PRIMARY KEY (LectureID, SubgroupKey)
    );
END;
"""

CREATE_STAGE_SQL = """
IF OBJECT_ID('tempdb..#FactLectureStage') IS NOT NULL DROP TABLE #FactLectureStage;
CREATE TABLE #FactLectureStage (
    LectureID     INT           NULL,
    DateKey       INT           NULL,
    FromTimeKey   INT           NULL,
    UntilTimeKey  INT           NULL,
    ClassKey      INT           NULL,
    SubgroupKey   INT           NULL,
    RoomKey       INT           NULL,
    ActivityKey   INT           NULL,
    UserCount     INT           NULL,
    TotalStudents INT           NULL
);
"""

INSERT_STAGE_SQL = """
INSERT INTO #FactLectureStage
(LectureID, DateKey, FromTimeKey, UntilTimeKey, ClassKey, SubgroupKey, RoomKey, ActivityKey, UserCount, TotalStudents)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

MERGE_SQL = """
MERGE dbo.FactLecture AS tgt
USING #FactLectureStage AS src
    ON tgt.LectureID = src.LectureID AND tgt.SubgroupKey = src.SubgroupKey
WHEN MATCHED THEN
    UPDATE SET
        tgt.DateKey       = src.DateKey,
        tgt.FromTimeKey   = src.FromTimeKey,
        tgt.UntilTimeKey  = src.UntilTimeKey,
        tgt.ClassKey      = src.ClassKey,
        tgt.RoomKey       = src.RoomKey,
        tgt.ActivityKey   = src.ActivityKey,
        tgt.UserCount     = src.UserCount,
        tgt.TotalStudents = src.TotalStudents
WHEN NOT MATCHED BY TARGET THEN
    INSERT (LectureID, DateKey, FromTimeKey, UntilTimeKey, ClassKey, SubgroupKey, RoomKey, ActivityKey, UserCount, TotalStudents)
    VALUES (src.LectureID, src.DateKey, src.FromTimeKey, src.UntilTimeKey, src.ClassKey, src.SubgroupKey, src.RoomKey, src.ActivityKey, src.UserCount, src.TotalStudents);
"""

def main():
    if not records:
        print("No valid FactLecture rows found. Nothing to load.")
        return

    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(CREATE_STAGE_SQL)

            cur.fast_executemany = True
            cur.executemany(INSERT_STAGE_SQL, records)
            cur.execute(MERGE_SQL)

        conn.commit()

    print(f"✅ Uploaded {len(records)} FactLecture rows into dbo.FactLecture.")

if __name__ == "__main__":
    main()
