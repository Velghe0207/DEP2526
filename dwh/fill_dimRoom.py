import pandas as pd
import pyodbc
from pathlib import Path

# ---------------- Config ----------------
CSV_PATH = Path("../data/cleaned/all_rooms.csv")

server = "localhost\\MSSQLSERVER2019"
database = "DEP2"
driver = "ODBC Driver 17 for SQL Server"

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=Yes;"
    "TrustServerCertificate=Yes;"
)

# --------------- Read & tidy CSV ---------------
df = pd.read_csv(
    CSV_PATH,
    na_values=["NULL", ""],   # turn "NULL"/"" into NaN
    keep_default_na=True
)

expected_cols = [
    "RoomKey","Building","RoomFloor","Code",
    "RoomName","Category","Capacity","Area"
]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    raise ValueError(f"CSV missing columns: {missing}")

df = df[expected_cols].copy()

# ✅ Filter 1: RoomName starts with "GSCHB"
df = df[df["RoomName"].astype(str).str.startswith("GSCHB", na=False)]
# ✅ Filter 2: Capacity must be present (not NULL/NaN)
df = df[df["Capacity"].notna()]

# Set dtypes
df["RoomKey"]   = df["RoomKey"].astype("int64")
df["Building"]  = df["Building"].astype("Int64")
df["RoomFloor"] = df["RoomFloor"].astype("Int64")
df["Code"]      = df["Code"].astype("string")
df["RoomName"]  = df["RoomName"].astype("string")
df["Category"]  = df["Category"].astype("string")
df["Capacity"]  = df["Capacity"].astype("Int64")
df["Area"]      = pd.to_numeric(df["Area"], errors="coerce").round(2)

# Convert pandas NA → Python None for pyodbc
records = []
for _, r in df.iterrows():
    records.append((
        int(r["RoomKey"]),
        None if pd.isna(r["Building"])  else int(r["Building"]),
        None if pd.isna(r["RoomFloor"]) else int(r["RoomFloor"]),
        None if pd.isna(r["Code"])      else str(r["Code"]),
        None if pd.isna(r["RoomName"])  else str(r["RoomName"]),
        None if pd.isna(r["Category"])  else str(r["Category"]),
        int(r["Capacity"]),  # guaranteed not-NA after filter
        None if pd.isna(r["Area"])      else float(r["Area"]),
    ))

print(f"Filtered dataset: {len(records)} GSCHB rooms with non-NULL Capacity.")

# --------------- SQL ---------------
CREATE_TABLE_SQL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'DimRoom' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.DimRoom (
        RoomKey   INT           NOT NULL CONSTRAINT PK_DimRoom PRIMARY KEY,
        Building  INT           NULL,
        RoomFloor INT           NULL,
        Code      NVARCHAR(50)  NULL,
        RoomName  NVARCHAR(100) NULL,
        Category  NVARCHAR(100) NULL,
        Capacity  INT           NULL,
        Area      DECIMAL(10,2) NULL
    );
END;
"""

MIGRATE_TYPES_SQL = """
IF EXISTS (SELECT 1 FROM sys.tables WHERE name='DimRoom' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom') AND c.name = 'Code'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    ) ALTER TABLE dbo.DimRoom ALTER COLUMN Code NVARCHAR(50) NULL;

    IF EXISTS (
        SELECT 1 FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom') AND c.name = 'RoomName'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    ) ALTER TABLE dbo.DimRoom ALTER COLUMN RoomName NVARCHAR(100) NULL;

    IF EXISTS (
        SELECT 1 FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom') AND c.name = 'Category'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    ) ALTER TABLE dbo.DimRoom ALTER COLUMN Category NVARCHAR(100) NULL;

    BEGIN TRY ALTER TABLE dbo.DimRoom ALTER COLUMN Building  INT NULL; END TRY BEGIN CATCH END CATCH;
    BEGIN TRY ALTER TABLE dbo.DimRoom ALTER COLUMN RoomFloor INT NULL; END TRY BEGIN CATCH END CATCH;
    BEGIN TRY ALTER TABLE dbo.DimRoom ALTER COLUMN Capacity  INT NULL; END TRY BEGIN CATCH END CATCH;
    BEGIN TRY ALTER TABLE dbo.DimRoom ALTER COLUMN Area      DECIMAL(10,2) NULL; END TRY BEGIN CATCH END CATCH;
END
"""

CREATE_STAGE_SQL = """
IF OBJECT_ID('tempdb..#DimRoomStage') IS NOT NULL DROP TABLE #DimRoomStage;
CREATE TABLE #DimRoomStage (
    RoomKey   INT           NOT NULL,
    Building  INT           NULL,
    RoomFloor INT           NULL,
    Code      NVARCHAR(50)  NULL,
    RoomName  NVARCHAR(100) NULL,
    Category  NVARCHAR(100) NULL,
    Capacity  INT           NULL,
    Area      DECIMAL(10,2) NULL
);
"""

INSERT_STAGE_SQL = """
INSERT INTO #DimRoomStage
(RoomKey, Building, RoomFloor, Code, RoomName, Category, Capacity, Area)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

MERGE_SQL = """
MERGE dbo.DimRoom AS tgt
USING #DimRoomStage AS src
    ON tgt.RoomKey = src.RoomKey
WHEN MATCHED THEN
    UPDATE SET
        tgt.Building  = src.Building,
        tgt.RoomFloor = src.RoomFloor,
        tgt.Code      = src.Code,
        tgt.RoomName  = src.RoomName,
        tgt.Category  = src.Category,
        tgt.Capacity  = src.Capacity,
        tgt.Area      = src.Area
WHEN NOT MATCHED BY TARGET THEN
    INSERT (RoomKey, Building, RoomFloor, Code, RoomName, Category, Capacity, Area)
    VALUES (src.RoomKey, src.Building, src.RoomFloor, src.Code, src.RoomName, src.Category, src.Capacity, src.Area);
"""

def main():
    if not records:
        print("No rooms match: RoomName starts with 'GSCHB' AND Capacity is not NULL. Nothing to load.")
        return

    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(MIGRATE_TYPES_SQL)
            cur.execute(CREATE_STAGE_SQL)

            cur.fast_executemany = True
            cur.executemany(INSERT_STAGE_SQL, records)
            cur.execute(MERGE_SQL)

        conn.commit()

    print(f"✅ Uploaded {len(records)} GSCHB rooms (with Capacity) into dbo.DimRoom.")

if __name__ == "__main__":
    main()
