import pandas as pd
import pyodbc
from pathlib import Path

# ---------------- Config ----------------
CSV_PATH = Path(r"D:\Documents2\School\26-EP3\DEP\repo\DEP2-2025-2026-groep12\00 data\00 raw\subgroups\all_subgroups_enriched.csv")

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
df = pd.read_csv(CSV_PATH)

# Drop stray embedded header rows and rows with a non-numeric SUBGROEPID
df = df[pd.to_numeric(df["SUBGROEPID"], errors="coerce").notna()]
df["SUBGROEPID"] = df["SUBGROEPID"].astype("int64")

# One row per subgroup: SubgroupKey in FactLecture is the raw SUBGROEPID itself
# (confirmed against dwh/lectures/FormattedLectures.csv), not a surrogate key.
df = df.drop_duplicates(subset=["SUBGROEPID"], keep="first")

# ProgramName: the richting/departement segment before the first "/" in the code
# (raw code already identifies richting + departement, no further decoding needed).
df["ProgramName"] = df["SUBGROEPCODE"].str.split("/").str[0].str.slice(0, 50)

records = [
    (int(r.SUBGROEPID), str(r.SUBGROEPCODE)[:50], str(r.ProgramName))
    for r in df.itertuples(index=False)
]

print(f"Prepared {len(records)} DimSubgroup rows.")

CREATE_STAGE_SQL = """
IF OBJECT_ID('tempdb..#DimSubgroupStage') IS NOT NULL DROP TABLE #DimSubgroupStage;
CREATE TABLE #DimSubgroupStage (
    SubgroupKey  INT          NOT NULL,
    SubgroupCode VARCHAR(50)  NOT NULL,
    ProgramName  VARCHAR(50)  NOT NULL
);
"""

INSERT_STAGE_SQL = """
INSERT INTO #DimSubgroupStage (SubgroupKey, SubgroupCode, ProgramName)
VALUES (?, ?, ?);
"""

MERGE_SQL = """
MERGE dbo.DimSubgroup AS tgt
USING #DimSubgroupStage AS src
    ON tgt.SubgroupKey = src.SubgroupKey
WHEN MATCHED THEN
    UPDATE SET tgt.SubgroupCode = src.SubgroupCode, tgt.ProgramName = src.ProgramName
WHEN NOT MATCHED BY TARGET THEN
    INSERT (SubgroupKey, SubgroupCode, ProgramName)
    VALUES (src.SubgroupKey, src.SubgroupCode, src.ProgramName);
"""


def main():
    if not records:
        print("No DimSubgroup rows to load.")
        return

    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(CREATE_STAGE_SQL)
            cur.fast_executemany = True
            cur.executemany(INSERT_STAGE_SQL, records)
            cur.execute(MERGE_SQL)
        conn.commit()

    print(f"Uploaded {len(records)} rows into dbo.DimSubgroup.")


if __name__ == "__main__":
    main()
