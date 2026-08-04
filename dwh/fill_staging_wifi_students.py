"""
One-time bulk load of the SharePoint-delivered full-year TIN data
(data/sharepoint/students_TIN_2526.parquet + data/sharepoint/wifi_TIN_2526.parquet)
into the DEP2_staging tables (DimUser, BridgeUserSubgroup, FactWifiConnection).

Replaces the old incremental scraping/wifi_script.py (API-based, 15-minute
cronjob) now that the school delivers the whole year as two parquet files
instead. wifi.username == students.email (verified: every wifi username is
present in the students' email column), so that's the join key for DimUser.
"""

import pandas as pd
import pyodbc

STUDENTS_PATH = "data/sharepoint/students_TIN_2526.parquet"
WIFI_PATH = "data/sharepoint/wifi_TIN_2526.parquet"

server = "localhost\\MSSQLSERVER2019"
database = "DEP2_staging"
driver = "ODBC Driver 17 for SQL Server"

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=Yes;"
    "TrustServerCertificate=Yes;"
)


def load_users_and_bridge(conn):
    students = pd.read_parquet(
        STUDENTS_PATH, columns=["subgroep_id", "email"]
    )
    students = students.dropna(subset=["email", "subgroep_id"])
    students["email"] = students["email"].str.strip()
    students["subgroep_id"] = pd.to_numeric(
        students["subgroep_id"], errors="coerce"
    )
    students = students.dropna(subset=["subgroep_id"])
    students["subgroep_id"] = students["subgroep_id"].astype("int64")

    emails = students["email"].drop_duplicates().tolist()
    print(f"Prepared {len(emails)} DimUser rows.")

    cur = conn.cursor()
    cur.execute("""
        IF OBJECT_ID('tempdb..#DimUserStage') IS NOT NULL DROP TABLE #DimUserStage;
        CREATE TABLE #DimUserStage (UserName VARCHAR(70) NOT NULL);
    """)
    cur.fast_executemany = True
    cur.executemany(
        "INSERT INTO #DimUserStage (UserName) VALUES (?);",
        [(e[:70],) for e in emails],
    )
    cur.fast_executemany = False
    cur.execute("""
        MERGE dbo.DimUser AS tgt
        USING #DimUserStage AS src
            ON tgt.UserName = src.UserName
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (UserName) VALUES (src.UserName);
    """)
    conn.commit()
    print("DimUser merged.")

    user_map = pd.read_sql("SELECT UserKey, UserName FROM dbo.DimUser", conn)
    students = students.merge(
        user_map, left_on="email", right_on="UserName", how="inner"
    )
    bridge = students[["UserKey", "subgroep_id"]].drop_duplicates()
    bridge_records = [
        (int(r.UserKey), int(r.subgroep_id)) for r in bridge.itertuples(index=False)
    ]
    print(f"Prepared {len(bridge_records)} BridgeUserSubgroup rows.")

    cur.execute("""
        IF OBJECT_ID('tempdb..#BridgeStage') IS NOT NULL DROP TABLE #BridgeStage;
        CREATE TABLE #BridgeStage (UserKey INT NOT NULL, SubgroupKey INT NOT NULL);
    """)
    cur.fast_executemany = True
    cur.executemany(
        "INSERT INTO #BridgeStage (UserKey, SubgroupKey) VALUES (?, ?);",
        bridge_records,
    )
    cur.fast_executemany = False
    cur.execute("""
        MERGE dbo.BridgeUserSubgroup AS tgt
        USING #BridgeStage AS src
            ON tgt.UserKey = src.UserKey AND tgt.SubgroupKey = src.SubgroupKey
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (UserKey, SubgroupKey) VALUES (src.UserKey, src.SubgroupKey);
    """)
    conn.commit()
    print("BridgeUserSubgroup merged.")

    return user_map


def load_wifi_connections(conn, user_map):
    wifi = pd.read_parquet(WIFI_PATH, columns=["timestamp", "username", "ssid"])
    wifi = wifi[wifi["ssid"] == "eduroam"]

    # Round to the minute: DimTime only has per-minute keys (seconds always 0),
    # and the UserCount matching window in SQLFillUserCountTotalStudents.sql
    # works at minute granularity anyway.
    ts = wifi["timestamp"].dt.round("min")
    wifi = wifi.assign(
        DateKey=ts.dt.strftime("%Y%m%d").astype("int64"),
        TimeKey=ts.dt.strftime("%H%M00").astype("int64"),
    )

    wifi = wifi.merge(
        user_map, left_on="username", right_on="UserName", how="inner"
    )
    wifi = wifi[["DateKey", "TimeKey", "UserKey"]].drop_duplicates()
    records = [
        (int(r.DateKey), int(r.TimeKey), int(r.UserKey))
        for r in wifi.itertuples(index=False)
    ]
    print(f"Prepared {len(records)} FactWifiConnection rows (after minute-rounding + dedup).")

    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE dbo.FactWifiConnection;")
    cur.fast_executemany = True
    cur.executemany(
        "INSERT INTO dbo.FactWifiConnection (DateKey, TimeKey, UserKey) VALUES (?, ?, ?);",
        records,
    )
    conn.commit()
    print(f"Loaded {len(records)} rows into dbo.FactWifiConnection.")


def main():
    with pyodbc.connect(conn_str, autocommit=False) as conn:
        user_map = load_users_and_bridge(conn)
        load_wifi_connections(conn, user_map)


if __name__ == "__main__":
    main()
