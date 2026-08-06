# fill_reservations.py
# ------------------------------------------------------------
# Reads reservations.csv and upserts rows into the DWH fact table
# Columns targeted (as in your screenshot):
#   FromTimeKey | UntilTimeKey | ProgramKey | DateKey | ClassKey |
#   SubgroupKey | RoomKey | ScheduleID | UserCount | TotalStudents | AttendanceRate (computed in SQL)
#
# Notes:
# - AttendanceRate is a computed column -> NOT written by this script.
# - DimTime lookup is robust and cached.
# - DimRoom.Code is assumed to be VARCHAR/NVARCHAR matching strings like '01.04.120.040'.
# - If "Rooms" has multiple codes, the first non-empty is used.

import csv
import datetime as dt
from typing import Optional, Tuple

import pyodbc

# -------------------- CONFIG --------------------
CSV_PATH = "../data/cleaned/all_TEreservations.csv"

SERVER = "localhost\\MSSQLSERVER2019"
DATABASE = "DEP2"
DRIVER = "ODBC Driver 17 for SQL Server"

TARGET_TABLE = "FactSchedule"  # change if your fact table has a different name

# If your DimTime has a known format for TimeKey, set one of these for speed:
#   "HHMMSS_INT" ->  08:30:00 ->  83000
#   "HHMM_INT"   ->  08:30:00 ->  830
#   None         ->  try multiple strategies automatically (default)
FORCE_TIMEKEY_FORMAT: Optional[str] = None

# -------------------- CONNECTION --------------------
def get_connection():
    return pyodbc.connect(
        f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=Yes;TrustServerCertificate=Yes"
    )

# -------------------- HELPERS --------------------
_timekey_cache = {}
_roomkey_cache = {}

def parse_dt(s: str) -> dt.datetime:
    return dt.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")

def to_datekey(d: dt.date) -> int:
    return int(d.strftime("%Y%m%d"))

def _fetch_timekey_auto(cur: pyodbc.Cursor, t: dt.time) -> Optional[int]:
    """Try several plausible DimTime schemas to find the TimeKey."""
    hhmmss_txt = f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}"
    hhmm_txt = f"{t.hour:02d}:{t.minute:02d}"
    hhmmss_int = t.hour * 10000 + t.minute * 100 + t.second
    hhmm_int = t.hour * 100 + t.minute

    # 1) Text columns that may exist
    for col in ("Time", "FullTime", "TimeText", "Time24"):
        try:
            cur.execute(f"SELECT TimeKey FROM DimTime WHERE {col} IN (?,?)", hhmmss_txt, hhmm_txt)
            row = cur.fetchone()
            if row:
                return int(row[0])
        except pyodbc.Error:
            pass

    # 2) Key equals HHMMSS
    try:
        cur.execute("SELECT TimeKey FROM DimTime WHERE TimeKey = ?", hhmmss_int)
        row = cur.fetchone()
        if row:
            return int(row[0])
    except pyodbc.Error:
        pass

    # 3) Key equals HHMM
    try:
        cur.execute("SELECT TimeKey FROM DimTime WHERE TimeKey = ?", hhmm_int)
        row = cur.fetchone()
        if row:
            return int(row[0])
    except pyodbc.Error:
        pass

    # 4) Hour/Minute columns
    try:
        cur.execute("SELECT TimeKey FROM DimTime WHERE Hour24 = ? AND Minute = ?", t.hour, t.minute)
        row = cur.fetchone()
        if row:
            return int(row[0])
    except pyodbc.Error:
        pass

    return None

def _fetch_timekey_forced(cur: pyodbc.Cursor, t: dt.time, mode: str) -> Optional[int]:
    if mode == "HHMMSS_INT":
        key = t.hour * 10000 + t.minute * 100 + t.second
        cur.execute("SELECT TimeKey FROM DimTime WHERE TimeKey = ?", key)
        row = cur.fetchone()
        return int(row[0]) if row else None
    if mode == "HHMM_INT":
        key = t.hour * 100 + t.minute
        cur.execute("SELECT TimeKey FROM DimTime WHERE TimeKey = ?", key)
        row = cur.fetchone()
        return int(row[0]) if row else None
    return None

def get_timekey(cur: pyodbc.Cursor, t: dt.time) -> int:
    """Resolve a TimeKey for a given time; cached per (h,m,s)."""
    k = (t.hour, t.minute, t.second)
    if k in _timekey_cache:
        return _timekey_cache[k]

    if FORCE_TIMEKEY_FORMAT:
        tk = _fetch_timekey_forced(cur, t, FORCE_TIMEKEY_FORMAT)
    else:
        tk = _fetch_timekey_auto(cur, t)

    if tk is None:
        raise RuntimeError(
            f"Could not resolve TimeKey for {t}. "
            "Adjust FORCE_TIMEKEY_FORMAT or update the lookup logic to match your DimTime schema."
        )
    _timekey_cache[k] = tk
    return tk

def get_roomkey_from_code(cur: pyodbc.Cursor, room_code: str) -> Optional[int]:
    """Find DimRoom.RoomKey by DimRoom.Code; falls back to REPLACE(Code,'.','')."""
    if not room_code:
        return None
    room_code = room_code.strip()
    if room_code in _roomkey_cache:
        return _roomkey_cache[room_code]

    # exact string match
    cur.execute("SELECT RoomKey FROM DimRoom WHERE Code = ?", room_code)
    row = cur.fetchone()
    if row:
        _roomkey_cache[room_code] = int(row[0])
        return _roomkey_cache[room_code]

    # fallback: remove dots
    code_nodots = room_code.replace(".", "")
    try:
        cur.execute("SELECT RoomKey FROM DimRoom WHERE REPLACE(Code, '.', '') = ?", code_nodots)
        row = cur.fetchone()
        if row:
            _roomkey_cache[room_code] = int(row[0])
            return _roomkey_cache[room_code]
    except pyodbc.Error:
        pass

    return None

def upsert_reservation(
    cur: pyodbc.Cursor,
    *,
    schedule_id: int,
    datekey: int,
    from_timekey: int,
    until_timekey: int,
    roomkey: Optional[int],
    programkey: Optional[int] = None,
    classkey: Optional[int] = None,
    subgroupkey: Optional[int] = None,
    usercount: Optional[int] = None,
    totalstudents: Optional[int] = None,
):
    """
    MERGE on ScheduleID to insert or update.
    IMPORTANT: AttendanceRate is computed in SQL, so it is NOT included here.
    """
    cur.execute(
        f"""
        MERGE {TARGET_TABLE} AS T
        USING (VALUES (?,?,?,?,?,?,?,?,?,?)) AS S
              (FromTimeKey, UntilTimeKey, ProgramKey, DateKey, ClassKey, SubgroupKey, RoomKey, ScheduleID, UserCount, TotalStudents)
        ON T.ScheduleID = S.ScheduleID
        WHEN MATCHED THEN UPDATE SET
            T.FromTimeKey   = S.FromTimeKey,
            T.UntilTimeKey  = S.UntilTimeKey,
            T.ProgramKey    = S.ProgramKey,
            T.DateKey       = S.DateKey,
            T.ClassKey      = S.ClassKey,
            T.SubgroupKey   = S.SubgroupKey,
            T.RoomKey       = S.RoomKey,
            T.UserCount     = S.UserCount,
            T.TotalStudents = S.TotalStudents
        WHEN NOT MATCHED THEN
            INSERT (FromTimeKey, UntilTimeKey, ProgramKey, DateKey, ClassKey, SubgroupKey, RoomKey, ScheduleID, UserCount, TotalStudents)
            VALUES (S.FromTimeKey, S.UntilTimeKey, S.ProgramKey, S.DateKey, S.ClassKey, S.SubgroupKey, S.RoomKey, S.ScheduleID, S.UserCount, S.TotalStudents);
        """,
        from_timekey,
        until_timekey,
        programkey,
        datekey,
        classkey,
        subgroupkey,
        roomkey,
        schedule_id,
        usercount,
        totalstudents,
    )

# -------------------- MAIN --------------------
def main():
    cnxn = get_connection()
    cnxn.autocommit = False
    cur = cnxn.cursor()

    # Load CSV
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    count = 0
    for r in rows:
        # Mandatory fields from CSV
        schedule_id = int(r["Id"])
        start_dt = parse_dt(r["Start"])
        end_dt = parse_dt(r["End"])

        # Keys for date/time
        datekey = to_datekey(start_dt.date())
        from_timekey = get_timekey(cur, start_dt.time())
        until_timekey = get_timekey(cur, end_dt.time())

        # Resolve RoomKey from Rooms (take first non-empty if multiple)
        rooms_raw = (r.get("Rooms") or "").strip()
        room_code = ""
        if rooms_raw:
            room_code = [x.strip() for x in rooms_raw.split(",") if x.strip()][0]
        roomkey = get_roomkey_from_code(cur, room_code)

        # Unknown/empty dimension metrics from this CSV -> NULLs
        programkey = None
        classkey = None
        subgroupkey = None
        usercount = None
        totalstudents = None

        upsert_reservation(
            cur,
            schedule_id=schedule_id,
            datekey=datekey,
            from_timekey=from_timekey,
            until_timekey=until_timekey,
            roomkey=roomkey,
            programkey=programkey,
            classkey=classkey,
            subgroupkey=subgroupkey,
            usercount=usercount,
            totalstudents=totalstudents,
        )
        count += 1

    cnxn.commit()
    print(f"Upserted {count} rows into {TARGET_TABLE}.")
    cur.close()
    cnxn.close()

if __name__ == "__main__":
    main()
