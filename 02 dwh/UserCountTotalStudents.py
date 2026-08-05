import sqlalchemy as sa

server = "localhost\\MSSQLSERVER2019"
database = "DEP2"
driver = "ODBC Driver 18 for SQL Server"

engine = sa.create_engine(
    f"mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes&TrustServerCertificate=yes"
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
