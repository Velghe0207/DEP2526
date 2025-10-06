import pandas as pd
from sqlalchemy import create_engine


def create_dim_time():
    # Alle uren en minuten
    hours = range(24)
    minutes = range(60)

    # hours en minutes combineren
    time_data = []
    for hour in hours:
        for minute in minutes:
            time_key = int(f"{hour:02}{minute:02}00")  # 000000 voor uren en minuten
            full_time = f"{hour:02}:{minute:02}:00"  # 00:00:00
            am_pm = "AM" if hour < 12 else "PM"
            time_data.append((time_key, hour, minute, 0, full_time, am_pm))

    # Dataframe aanmaken
    dim_time = pd.DataFrame(
        time_data,
        columns=["TimeKey", "Hour", "Minutes", "Seconds", "FullTime", "TimeAM_PM"],
    )

    return dim_time


# Functie create_dim_time() uitvoeren
dim_time_df = create_dim_time()

# SQL Server configuratie (lokaal testen - pas aan voor je eigen SQL server)
# server = "127.0.0.1,1500"
# database = "DEP"
# username = "SA"
# password = "Passwordgroep21!"
# driver = "ODBC Driver 17 for SQL Server"

# Verbinden met de database aan de hand van sqlalchemy
# engine = create_engine(
#     f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"
# )

server = "LAPTOP-R1GLLN97"
database = "loltest2"
driver = "ODBC Driver 17 for SQL Server"

# Maak een database-engine
engine = create_engine(
    f"mssql+pyodbc://@{server}/{database}?trusted_connection=yes&driver={driver}"
)

# DataFrame naar SQL Server wegschrijven
dim_time_df.to_sql("DimTime", engine, if_exists="append", index=False)

print("DimTime DataFrame succesvol weggeschreven")
