import pandas as pd
from sqlalchemy import create_engine


def create_dim_date(start_date="2025-01-01", end_date="2026-12-31"):
    # Genereer een datumreeks
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    # Maanden en dagen in het Nederlands en Engels
    months_nl = {
        "January": "Januari",
        "February": "Februari",
        "March": "Maart",
        "April": "April",
        "May": "Mei",
        "June": "Juni",
        "July": "Juli",
        "August": "Augustus",
        "September": "September",
        "October": "Oktober",
        "November": "November",
        "December": "December",
    }

    days_nl = {
        "Monday": "Maandag",
        "Tuesday": "Dinsdag",
        "Wednesday": "Woensdag",
        "Thursday": "Donderdag",
        "Friday": "Vrijdag",
        "Saturday": "Zaterdag",
        "Sunday": "Zondag",
    }

    def get_season(date):
        month = date.month
        day = date.day
        if (
            (month == 12 and day >= 21)
            or (month in [1, 2])
            or (month == 3 and day <= 20)
        ):
            return "Winter"
        elif (
            (month == 3 and day >= 21)
            or (month in [4, 5])
            or (month == 6 and day <= 20)
        ):
            return "Spring"
        elif (
            (month == 6 and day >= 21)
            or (month in [7, 8])
            or (month == 9 and day <= 22)
        ):
            return "Summer"
        else:
            return "Fall"

    # Maak een DataFrame
    dim_date = pd.DataFrame(
        {
            "DateKey": date_range.strftime("%Y%m%d").astype(int),
            "FullDate": date_range,
            "NameDay": date_range.strftime("%A"),
            "NameMonthDutch": date_range.strftime("%B").map(months_nl),
            "NameMonthEN": date_range.strftime("%B"),
            "NameDayDutch": date_range.strftime("%A").map(days_nl),
            "NameDayEN": date_range.strftime("%A"),
            "NameQuarter": date_range.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}),
            "NumberQuarter": date_range.quarter,
            "NumberSemester": date_range.month.map({1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 1, 10: 1, 11: 1, 12: 1}),
            "Day": date_range.day,
            "Month": date_range.month,
            "Year": date_range.year,
            "Weekday": date_range.weekday + 1,  # Maandag = 1, Zondag = 7
            "DayOfYear": date_range.dayofyear,
            "Season": date_range.map(get_season),
        }
    )

    return dim_date


# Aanmaken van de DimDate DataFrame
dim_date_df = create_dim_date()

# SQL Server configuratie (pas aan voor je eigen SQL server)
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
dim_date_df.to_sql("DimDate", engine, if_exists="append", index=False)

print("Dataframe succesvol weggeschreven")
