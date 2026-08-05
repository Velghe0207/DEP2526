import ast
import re

import pandas as pd
import pyodbc
from pathlib import Path

# ---------------- Config ----------------
CSV_PATH = Path("data/cleaned/all_courses.csv")

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
# One row per OLOD/course code already (no duplicate codes) - do NOT explode by
# faculty like the old class_processing.ipynb did, that created duplicate
# ClassCode rows with different ClassKeys and broke the FormatLectures.py join.
df = pd.read_csv(CSV_PATH)
df = df.drop_duplicates(subset=["code"], keep="first")


def first_program_stage(faculties_str):
    """Trajectschijf number of the first listed faculty, if any."""
    try:
        faculties = ast.literal_eval(faculties_str)
    except (ValueError, SyntaxError):
        return None
    if not faculties:
        return None
    match = re.search(r"trajectschijf (\d+)", faculties[0])
    return int(match.group(1)) if match else None


df["ClassProgramStage"] = df["faculties"].apply(first_program_stage).astype("Int64")
df["ClassCredits"] = (
    df["credits"].astype(str).str.extract(r"(\d+)").astype("Int64")
)
df["ClassSecondChance"] = df["second_chance"].map(
    {"wel mogelijk.": True, "niet mogelijk.": False}
).fillna(False)
df["ClassKey"] = range(1, len(df) + 1)

records = [
    (
        int(r.ClassKey),
        str(r.title)[:150],
        int(r.code),
        None if pd.isna(r.ClassCredits) else int(r.ClassCredits),
        bool(r.ClassSecondChance),
        None if pd.isna(r.ClassProgramStage) else int(r.ClassProgramStage),
    )
    for r in df.itertuples(index=False)
]

print(f"Prepared {len(records)} DimClass rows.")

CREATE_STAGE_SQL = """
IF OBJECT_ID('tempdb..#DimClassStage') IS NOT NULL DROP TABLE #DimClassStage;
CREATE TABLE #DimClassStage (
    ClassKey          INT           NOT NULL,
    ClassName         VARCHAR(150)  NOT NULL,
    ClassCode         INT           NOT NULL,
    ClassCredits      INT           NULL,
    ClassSecondChance BIT           NOT NULL,
    ClassProgramStage INT           NULL
);
"""

INSERT_STAGE_SQL = """
INSERT INTO #DimClassStage
(ClassKey, ClassName, ClassCode, ClassCredits, ClassSecondChance, ClassProgramStage)
VALUES (?, ?, ?, ?, ?, ?);
"""

MERGE_SQL = """
MERGE dbo.DimClass AS tgt
USING #DimClassStage AS src
    ON tgt.ClassCode = src.ClassCode
WHEN MATCHED THEN
    UPDATE SET
        tgt.ClassName         = src.ClassName,
        tgt.ClassCredits      = src.ClassCredits,
        tgt.ClassSecondChance = src.ClassSecondChance,
        tgt.ClassProgramStage = src.ClassProgramStage
WHEN NOT MATCHED BY TARGET THEN
    INSERT (ClassKey, ClassName, ClassCode, ClassCredits, ClassSecondChance, ClassProgramStage)
    VALUES (src.ClassKey, src.ClassName, src.ClassCode, src.ClassCredits, src.ClassSecondChance, src.ClassProgramStage);
"""


def main():
    if not records:
        print("No DimClass rows to load.")
        return

    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(CREATE_STAGE_SQL)
            cur.fast_executemany = True
            cur.executemany(INSERT_STAGE_SQL, records)
            cur.fast_executemany = False
            cur.execute(MERGE_SQL)
        conn.commit()

    print(f"Uploaded {len(records)} rows into dbo.DimClass.")


if __name__ == "__main__":
    main()
