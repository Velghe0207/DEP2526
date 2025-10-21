import pandas as pd
import pyodbc
from pathlib import Path

# ---------------- Config ----------------
CSV_PATH = Path("../data/cleaned/lokalen/lokalen_cleaned.csv")

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
    na_values=["NULL", ""],
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

# Set dtypes
df["RoomKey"]   = df["RoomKey"].astype("int64")
df["Building"]  = df["Building"].astype("Int64")
df["RoomFloor"] = df["RoomFloor"].astype("Int64")
df["Code"]      = df["Code"].astype("string")
df["RoomName"]  = df["RoomName"].astype("string")
df["Category"]  = df["Category"].astype("string")
df["Capacity"]  = df["Capacity"].astype("Int64")
df["Area"]      = pd.to_numeric(df["Area"], errors="coerce").round(2)

records = []
for _, r in df.iterrows():
    records.append((
        int(r["RoomKey"]),
        None if pd.isna(r["Building"])  else int(r["Building"]),
        None if pd.isna(r["RoomFloor"]) else int(r["RoomFloor"]),
        None if pd.isna(r["Code"])      else str(r["Code"]),
        None if pd.isna(r["RoomName"])  else str(r["RoomName"]),
        None if pd.isna(r["Category"])  else str(r["Category"]),
        None if pd.isna(r["Capacity"])  else int(r["Capacity"]),
        None if pd.isna(r["Area"])      else float(r["Area"]),
    ))

# --------------- T-SQL blocks ---------------
# Create table if missing
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

# If the table already exists but has wrong datatypes, fix them safely.
# (Your error is due to Code not being NVARCHAR.)
MIGRATE_TYPES_SQL = """
IF EXISTS (SELECT 1 FROM sys.tables WHERE name='DimRoom' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    -- Make text columns NVARCHAR if they aren't already
    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom')
          AND c.name = 'Code'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    )
    BEGIN
        ALTER TABLE dbo.DimRoom ALTER COLUMN Code NVARCHAR(50) NULL;
    END

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom')
          AND c.name = 'RoomName'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    )
    BEGIN
        ALTER TABLE dbo.DimRoom ALTER COLUMN RoomName NVARCHAR(100) NULL;
    END

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom')
          AND c.name = 'Category'
          AND t.name NOT IN ('nvarchar','varchar','nchar','char')
    )
    BEGIN
        ALTER TABLE dbo.DimRoom ALTER COLUMN Category NVARCHAR(100) NULL;
    END

    -- Ensure numeric columns are INT/DECIMAL as expected
    -- (This is idempotent if already INT/DECIMAL(10,2))
    BEGIN TRY
        ALTER TABLE dbo.DimRoom ALTER COLUMN Building  INT NULL;
    END TRY BEGIN CATCH END CATCH;

    BEGIN TRY
        ALTER TABLE dbo.DimRoom ALTER COLUMN RoomFloor INT NULL;
    END TRY BEGIN CATCH END CATCH;

    BEGIN TRY
        ALTER TABLE dbo.DimRoom ALTER COLUMN Capacity  INT NULL;
    END TRY BEGIN CATCH END CATCH;

    -- If Area is not DECIMAL(10,2), fix it
    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.DimRoom')
          AND c.name = 'Area'
          AND NOT (t.name IN ('decimal','numeric') AND c.scale = 2 AND c.precision = 10)
    )
    BEGIN
        ALTER TABLE dbo.DimRoom ALTER COLUMN Area DECIMAL(10,2) NULL;
    END
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
    VALUES (src.RoomKey, src.Building, src.RoomFloor, src.Code, src.RoomName, src.Category, src.Capacity, src.Area)
OUTPUT $action AS MergeAction, inserted.RoomKey;
"""

def main():
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            # Ensure table exists, then migrate types if needed
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(MIGRATE_TYPES_SQL)

            # Stage and bulk load
            cur.execute(CREATE_STAGE_SQL)
            cur.fast_executemany = True
            cur.executemany(INSERT_STAGE_SQL, records)

            # Upsert
            cur.execute(MERGE_SQL)

        conn.commit()

    print(f"Upserted {len(records)} rows from '{CSV_PATH.name}' into dbo.DimRoom.")

if __name__ == "__main__":
    main()
