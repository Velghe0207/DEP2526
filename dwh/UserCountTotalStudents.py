import sqlalchemy as sa

server = "127.0.0.1"
database = "DEP2"
username = "sa"
password = "dep2025-G12"
driver = "ODBC Driver 18 for SQL Server"

engine = sa.create_engine(
    f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
)

# Read SQL file
with open("dwh/SQLFillUserCountTotalStudents.sql", "r", encoding="utf-8-sig") as file:
    sql_query = file.read()

# Remove any GO statements
sql_query = sql_query.replace("GO", "")

# Execute SQL
with engine.connect() as conn:
    with conn.begin():
        conn.execute(sa.text(sql_query))

print("UserCount and TotalStudents updated successfully.")

engine.dispose()
