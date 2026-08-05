"""
Bulk load the September 2025 backfill (data/week1_4_wifi/*.parquet, days
2025-09-25 through 2025-10-15) into DEP2_staging, extending FactWifiConnection
coverage before wifi_TIN_2526.parquet's data starts (2025-10-15).

IMPORTANT: this backfill uses a DIFFERENT, older pseudonymization scheme
("u_<sha256>") than the SharePoint export used everywhere else this year
("enc_<...>"). There is no crosswalk between the two schemes, so these are
loaded as separate DimUser identities, linked to their subgroup via the OLD
data/cleaned/all_students.csv (same "u_" scheme, SUBGROEPID is unaffected by
the pseudonymization change since it's the school's own class-group id).

Because of this, these legacy users must NOT be counted in FactLecture's
TotalStudents (the roster size) - that stays anchored to the current-scheme
("enc_") roster from students_TIN_2526.parquet, otherwise every subgroup's
TotalStudents would double-count the same real students under two identities
for the whole year. See the "u_"/"enc_" filter added to SQLFillUserCountTotalStudents.sql.
They ARE still useful as the UserCount numerator for lectures in this date
range, via BridgeUserSubgroup.
"""

import glob

import pandas as pd
import pyodbc

WEEK1_4_DIR = "data/week1_4_wifi"
OLD_STUDENTS_PATH = "data/cleaned/all_students.csv"

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


def load_wifi():
    files = sorted(glob.glob(f"{WEEK1_4_DIR}/*.parquet"))
    frames = []
    for f in files:
        df = pd.read_parquet(f, columns=["email", "timestamp", "ssid"])
        df = df[df["ssid"] == "eduroam"]
        df = df[df["email"].astype(str).str.len() > 0]
        frames.append(df)
    wifi = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(wifi)} eduroam rows from {len(files)} week1_4 files.")

    ts = pd.to_datetime(wifi["timestamp"]).dt.round("min")
    wifi = wifi.assign(
        DateKey=ts.dt.strftime("%Y%m%d").astype("int64"),
        TimeKey=ts.dt.strftime("%H%M00").astype("int64"),
    )
    return wifi[["email", "DateKey", "TimeKey"]].drop_duplicates()


def load_legacy_bridge(legacy_emails):
    old_students = pd.read_csv(OLD_STUDENTS_PATH)
    old_students = old_students[old_students["EMAIL"].isin(legacy_emails)]
    bridge = old_students[["EMAIL", "SUBGROEPID"]].drop_duplicates()
    bridge["SUBGROEPID"] = pd.to_numeric(bridge["SUBGROEPID"], errors="coerce")
    bridge = bridge.dropna(subset=["SUBGROEPID"])
    bridge["SUBGROEPID"] = bridge["SUBGROEPID"].astype("int64")
    return bridge


def main():
    wifi = load_wifi()
    legacy_emails = wifi["email"].unique().tolist()
    print(f"{len(legacy_emails)} unique legacy (u_) identities.")

    bridge = load_legacy_bridge(legacy_emails)
    print(f"Prepared {len(bridge)} legacy BridgeUserSubgroup rows.")

    with pyodbc.connect(conn_str, autocommit=False) as conn:
        cur = conn.cursor()

        # DimUser: add legacy identities not already present
        cur.execute("""
            IF OBJECT_ID('tempdb..#LegacyUserStage') IS NOT NULL DROP TABLE #LegacyUserStage;
            CREATE TABLE #LegacyUserStage (UserName VARCHAR(70) NOT NULL);
        """)
        cur.fast_executemany = True
        cur.executemany(
            "INSERT INTO #LegacyUserStage (UserName) VALUES (?);",
            [(e[:70],) for e in legacy_emails],
        )
        cur.fast_executemany = False
        cur.execute("""
            MERGE dbo.DimUser AS tgt
            USING #LegacyUserStage AS src
                ON tgt.UserName = src.UserName
            WHEN NOT MATCHED BY TARGET THEN
                INSERT (UserName) VALUES (src.UserName);
        """)
        conn.commit()
        print("Legacy DimUser rows merged.")

        user_map = pd.read_sql("SELECT UserKey, UserName FROM dbo.DimUser", conn)

        # BridgeUserSubgroup for legacy users
        bridge = bridge.merge(user_map, left_on="EMAIL", right_on="UserName", how="inner")
        bridge_records = [
            (int(r.UserKey), int(r.SUBGROEPID)) for r in bridge.itertuples(index=False)
        ]
        cur.execute("""
            IF OBJECT_ID('tempdb..#LegacyBridgeStage') IS NOT NULL DROP TABLE #LegacyBridgeStage;
            CREATE TABLE #LegacyBridgeStage (UserKey INT NOT NULL, SubgroupKey INT NOT NULL);
        """)
        cur.fast_executemany = True
        cur.executemany(
            "INSERT INTO #LegacyBridgeStage (UserKey, SubgroupKey) VALUES (?, ?);",
            bridge_records,
        )
        cur.fast_executemany = False
        cur.execute("""
            MERGE dbo.BridgeUserSubgroup AS tgt
            USING #LegacyBridgeStage AS src
                ON tgt.UserKey = src.UserKey AND tgt.SubgroupKey = src.SubgroupKey
            WHEN NOT MATCHED BY TARGET THEN
                INSERT (UserKey, SubgroupKey) VALUES (src.UserKey, src.SubgroupKey);
        """)
        conn.commit()
        print(f"Merged {len(bridge_records)} legacy BridgeUserSubgroup rows.")

        # FactWifiConnection for legacy users
        wifi = wifi.merge(user_map, left_on="email", right_on="UserName", how="inner")
        wifi_records = [
            (int(r.DateKey), int(r.TimeKey), int(r.UserKey))
            for r in wifi[["DateKey", "TimeKey", "UserKey"]].drop_duplicates().itertuples(index=False)
        ]
        cur.fast_executemany = True
        cur.executemany(
            """
            IF NOT EXISTS (SELECT 1 FROM dbo.FactWifiConnection WHERE DateKey=? AND TimeKey=? AND UserKey=?)
            INSERT INTO dbo.FactWifiConnection (DateKey, TimeKey, UserKey) VALUES (?, ?, ?);
            """,
            [(dk, tk, uk, dk, tk, uk) for dk, tk, uk in wifi_records],
        )
        conn.commit()
        print(f"Inserted {len(wifi_records)} legacy FactWifiConnection rows.")


if __name__ == "__main__":
    main()
