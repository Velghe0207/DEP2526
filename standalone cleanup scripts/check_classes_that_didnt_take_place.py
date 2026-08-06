import pyodbc

# ---------------------------------------------------------------------
# SQL SERVER
# ---------------------------------------------------------------------

SERVER = r"localhost\MSSQLSERVER2019"
DATABASE = "DEP2"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

connection = pyodbc.connect(CONNECTION_STRING)
cursor = connection.cursor()

cursor.execute("""
    SELECT
        C.ClassKey,
        C.ClassCode,
        C.ClassName
    FROM dbo.DimClass AS C
    LEFT JOIN dbo.FactLecture AS FL
        ON FL.ClassKey = C.ClassKey
    WHERE FL.ClassKey IS NULL
    ORDER BY C.ClassName;
""")

rows = cursor.fetchall()

print(f"\nAantal classes zonder lessen: {len(rows)}\n")

print(f"{'ClassKey':<10} {'ClassCode':<10} ClassName")
print("-" * 80)

for row in rows:
    print(
        f"{row.ClassKey:<10} "
        f"{str(row.ClassCode):<10} "
        f"{row.ClassName}"
    )

connection.close()