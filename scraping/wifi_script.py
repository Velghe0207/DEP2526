from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import requests
import pandas as pd
import time

# Loading environment variables from .env file
load_dotenv()


# Function for POST request to get access token using secret
def get_token(secret: str, url: str = "https://dep.simondg.com/auth/login"):
    response = requests.post(url, json={"secret": secret})
    response.raise_for_status()  # Raises an error if the request fails
    return response.json()["access_token"]


# Function for GET request to WiFi API
def get_wifi_clients(
    token: str, url: str = "https://dep.simondg.com/wifi-clients/last-30-minutes"
):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises an error if the request fails
    data = response.json()
    return pd.DataFrame(data)


def main():

    # SQL Server configuratie via pymssql (werkt zonder ODBC driver)
    server = "127.0.0.1"  # of 'ubuntu' als dat werkt
    port = 1500
    database = "DEP2_staging"
    username = "sa"
    password = "dep2025-G12"

    # SQLAlchemy engine via pymssql
    engine = create_engine(f"mssql+pymssql://{username}:{password}@{server}:{port}/{database}")

    # # SQL Server configuratie (lokaal testen - pas aan voor je eigen SQL server)
    # server = "127.0.0.1,1500"
    # database = "DEP2_staging"
    # username = "sa"
    # password = "dep2025-G12"
    # driver = "ODBC Driver 17 for SQL Server"

    # # Verbinden met de database aan de hand van sqlalchemy
    # engine = create_engine(
    #     f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"
    # )

    # SQL Server configuratie (pas aan voor je eigen SQL server)
    # server = "ubuntu"
    # database = "DEP2_staging"
    # username = "sa"
    # password = "dep2025-G12"
    # driver = "ODBC Driver 18 for SQL Server"

    # Verbinden met de database aan de hand van sqlalchemy
    # engine = create_engine(
    #     f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
    # )

    # Saving secret in a variable
    secret = os.getenv("SECRET")
    if not secret:
        raise ValueError("SECRET not found in .env file")

    token = get_token(secret)

    # Fetching WiFi clients data and filtering for 'eduroam' SSID
    df_wifi = get_wifi_clients(token)
    df_wifi_edu = df_wifi[df_wifi["ssid"] == "eduroam"]

    # Adjust timestamp to +2 hours for your timezone and round to the nearest minute
    df_wifi_edu["timestamp"] = (
        pd.to_datetime(df_wifi_edu["timestamp"]) + timedelta(hours=2)
    ).dt.round("T")

    # Generate DateKey and TimeKey
    df_wifi_edu["DateKey"] = df_wifi_edu["timestamp"].dt.strftime("%Y%m%d").astype(int)
    df_wifi_edu["TimeKey"] = df_wifi_edu["timestamp"].dt.strftime("%H%M%S").astype(int)

    # Fetch existing DimUser data
    existing_users = pd.read_sql("SELECT UserKey, UserName FROM DimUser", engine)

    # Create a dictionary of existing usernames and their UserKeys
    existing_user_mapping = dict(zip(existing_users["UserName"], existing_users["UserKey"]))

    # Generate UserKey starting from the last UserKey
    max_user_key = max(existing_user_mapping.values(), default=0)
    new_user_mapping = {
        username: idx + 1 + max_user_key
        for idx, username in enumerate(df_wifi_edu["username"].unique())
        if username not in existing_user_mapping
    }

    # Combine existing and new user mappings
    user_mapping = {**existing_user_mapping, **new_user_mapping} # ** is used to unpack dictionaries
    df_wifi_edu["UserKey"] = df_wifi_edu["username"].map(user_mapping)

    # Create DimUser table (only for new users)
    dim_user = pd.DataFrame(
        list(new_user_mapping.items()), columns=["UserName", "UserKey"]
    )[["UserKey", "UserName"]]

    # Create FactWifiConnection table
    fact_wifi_connection = df_wifi_edu[["DateKey", "TimeKey", "UserKey"]]
    fact_wifi_connection = fact_wifi_connection.drop_duplicates().reset_index(drop=True)

    # Writing to csv files
    # filename = f"data/wifi_clients/wifi_clients_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    # df_wifi.to_csv(filename, index=False)
    # dim_user.to_csv("DimUser.csv", index=False)
    # fact_wifi_connection.to_csv("FactWifiConnection.csv", index=False)

    # server = "LAPTOP-R1GLLN97"
    # database = "loltest2"
    # driver = "ODBC Driver 17 for SQL Server"

    # # Creation of database engine
    # engine = create_engine(
    #     f"mssql+pyodbc://@{server}/{database}?trusted_connection=yes&driver={driver}"
    # )

    # Writing dataframes to SQL Server
    dim_user.to_sql("DimUser", engine, if_exists="append", index=False)
    fact_wifi_connection.to_sql(
        "FactWifiConnection", engine, if_exists="append", index=False
    )

    print("Dataframe succesvol weggeschreven")


if __name__ == "__main__":
    main()
