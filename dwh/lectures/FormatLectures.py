import pandas as pd
import pyodbc
import os
from datetime import datetime
from dateutil import parser

print(os.getcwd())
# ============================================================
# 1️⃣ CONFIGURATION
# ============================================================
RAW_CSV = "dwh/lectures/AllLectures.csv"
OUTPUT_CSV = "dwh/lectures/FormattedLectures.csv"
MISSING_KEYS_CSV = "dwh/lectures/FormattedLectures_missingRoomOrClass.csv"

SERVER = "localhost\\MSSQLSERVER2019"
DATABASE = "DEP2"
DRIVER = "ODBC Driver 17 for SQL Server"

# ============================================================
# 2️⃣ LOAD RAW DATA
# ============================================================
import csv

df = pd.read_csv(
    "dwh/lectures/alllectures.csv",
    sep=";",                # your separator is semicolon
    quoting=csv.QUOTE_NONE, # disables special treatment of quotes
    on_bad_lines="skip",    # optionally skip malformed lines
    engine="python"         # needed when disabling quoting
    # dtype=str
)

# Drop irrelevant columns
drop_cols = [
    'Updated','UpdatedBy','Status','ReasonTeacher','ReasonRoom','InternExtern','Department','User',
    'CoordinationService','ContactPerson','MobileEquipment','GroupHogent','Person','Student','Invigilator'
]
df = df.drop(columns=drop_cols)

# ============================================================
# 3️⃣ CREATE REQUIRED COLUMNS
# ============================================================
df = df.rename(columns={'Id': 'LectureId'})

def parse_datetime_safe(date_str):
    """Parses date/time."""
    return datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")

df['ParsedStart'] = df['Start'].apply(parse_datetime_safe)
df['ParsedEnd'] = df['End'].apply(parse_datetime_safe)

df['DateKey'] = df['ParsedStart'].dt.strftime("%Y%m%d").astype('Int64')
df['FromTimeKey'] = df['ParsedStart'].dt.strftime("%H%M%S").astype('Int64')
df['UntilTimeKey'] = df['ParsedEnd'].dt.strftime("%H%M%S").astype('Int64')

df.loc[df['LectureId'] == "479883", 'OlodPointers'] = '193745'

# ============================================================
# 4️⃣ SPLIT MULTIPLE SUBGROUPS INTO MULTIPLE ROWS
# ============================================================
def split_subgroups(val):
    if pd.isna(val) or val.strip() == "":
        return [None]
    if "|" in val:
        return [v.strip() for v in val.split("|") if v.strip()]
    return [val.strip()]

df = df.assign(SubgroupKey=df['Classgroups'].apply(split_subgroups))
df = df.explode('SubgroupKey')
df = df.drop(columns=['Classgroups'])

# ============================================================
# 5️⃣ CONNECT TO DATABASE TO GET FOREIGN KEYS
# ============================================================
conn_str = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=Yes;TrustServerCertificate=Yes"
conn = pyodbc.connect(conn_str)

class_map = pd.read_sql("SELECT ClassCode, ClassKey FROM dbo.DimClass", conn)
room_map = pd.read_sql("SELECT Code AS RoomCode, RoomKey FROM dbo.DimRoom", conn)
activity_map = pd.read_sql("SELECT ActivityKey, SourceColumn, SourceValue FROM dbo.DimActivity", conn)
conn.close()

# Merge ClassKey from OlodPointers (take the first code when a lecture lists
# several pipe-separated OLODs; ClassKey isn't part of the FactLecture PK
# anyway, so any duplicate LectureId+SubgroupKey rows this could create are
# collapsed later in fillFactLectures.py).
df['OlodPointers'] = pd.to_numeric(
    df['OlodPointers'].astype(str).str.split('|').str[0], errors='coerce'
).astype('Int64')
class_map['ClassCode'] = class_map['ClassCode'].astype('Int64')
df = df.merge(class_map, how='left', left_on='OlodPointers', right_on='ClassCode')
df = df.drop(columns=['ClassCode'])

# Merge RoomKey from Rooms (take the first room when a lecture lists several
# pipe-separated rooms, same reasoning as OlodPointers above).
df['Rooms'] = df['Rooms'].astype(str).str.split('|').str[0]
df = df.merge(room_map, how='left', left_on='Rooms', right_on='RoomCode')
df = df.drop(columns=['RoomCode'])

# ============================================================
# 6️⃣ DETERMINE ActivityKey BASED ON SOURCE COLUMNS
# ============================================================
def find_activity_key(row):
    for col in ['WorkFormCourse','WorkFormExam','WorkFormEvaluation','EducationActivity','LearningEnvironment','ExamEnvironment']:
        val = row.get(col)
        if pd.notna(val) and val != '':
            match = activity_map[
                (activity_map['SourceColumn'] == col) &
                (activity_map['SourceValue'] == val)
            ]
            if not match.empty:
                return match['ActivityKey'].iloc[0]
    default = activity_map[activity_map['SourceValue'] == '']
    return default['ActivityKey'].iloc[0] if not default.empty else None

df['ActivityKey'] = df.apply(find_activity_key, axis=1)

# ============================================================
# 7️⃣ FILL MISSING/EMPTY COLUMNS
# ============================================================
df['UserCount'] = None
df['TotalStudents'] = None
df['AttendanceRate'] = None

final_columns = [
    'LectureId','DateKey','FromTimeKey','UntilTimeKey',
    'ClassKey','SubgroupKey','RoomKey','ActivityKey',
    'UserCount','TotalStudents','AttendanceRate'
]
df_final = df[final_columns]

# Clean numeric keys
df_final['ClassKey'] = pd.to_numeric(df_final['ClassKey'], errors='coerce').astype('Int64')
df_final['RoomKey'] = pd.to_numeric(df_final['RoomKey'], errors='coerce').astype('Int64')

# ============================================================
# 8️⃣ SPLIT VALID / INVALID ROWS (RoomKey or ClassKey missing)
# ============================================================
invalid_df = df_final[df_final['RoomKey'].isna() | df_final['ClassKey'].isna()]
valid_df = df_final.drop(invalid_df.index)

# Save both files
valid_df.to_csv(OUTPUT_CSV, sep=';', index=False, encoding='utf-8-sig')
invalid_df.to_csv(MISSING_KEYS_CSV, sep=';', index=False, encoding='utf-8-sig')

# ============================================================
# 9️⃣ PRINT SUMMARY
# ============================================================
print("✅ Formatting complete!")
print(f"➡️ Cleaned output saved to: {OUTPUT_CSV}")
print(f"➡️ Invalid rows saved to: {MISSING_KEYS_CSV}")
print(f"Total rows processed: {len(df_final)}")
print(f"Valid rows: {len(valid_df)}")
print(f"Invalid rows (missing RoomKey or ClassKey): {len(invalid_df)}")
print()
print("📊 Missing key breakdown:")
print(f"  - Missing ClassKeys: {df_final['ClassKey'].isna().sum()}")
print(f"  - Missing RoomKeys:  {df_final['RoomKey'].isna().sum()}")
print(f"  - Missing ActivityKeys: {df_final['ActivityKey'].isna().sum()}")
