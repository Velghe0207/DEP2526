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

    # SQL Server config binnen de VM
    server = "127.0.0.1"  
    database = "DEP2_staging"
    username = "sa"
    password = "dep2025-G12"
    driver = "ODBC Driver 18 for SQL Server"

    # SQLAlchemy engine using ODBC
    engine = create_engine(
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
    )

    # # SQL Server configuratie (Tunnel forwarding)
    # server = "127.0.0.1,1500"
    # database = "DEP2_staging"
    # username = "sa"
    # password = "dep2025-G12"
    # driver = "ODBC Driver 17 for SQL Server"

    # # Verbinden met de database aan de hand van sqlalchemy
    # engine = create_engine(
    #     f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"
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

    # Fetch existing usernames from DimUser
    existing_usernames = pd.read_sql("SELECT UserName FROM DimUser", engine)["UserName"]

    # Find only new usernames
    new_users = df_wifi_edu.loc[
        ~df_wifi_edu["username"].isin(existing_usernames), ["username"]
    ].drop_duplicates()
    new_users = new_users.rename(columns={"username": "UserName"})

    # Insert new users
    if not new_users.empty:
        new_users.to_sql("DimUser", engine, if_exists="append", index=False)
        print(f"Added {len(new_users)} new users to DimUser.")
    else:
        print("No new users to add.")

    # Fetch all UserKeys from DimUser and map them to the correct usernames
    all_users = pd.read_sql("SELECT UserKey, UserName FROM DimUser", engine)
    user_mapping = dict(zip(all_users["UserName"], all_users["UserKey"]))
    df_wifi_edu["UserKey"] = df_wifi_edu["username"].map(user_mapping)

    # FactWiFiConnection table
    fact_wifi_connection = (
        df_wifi_edu[["DateKey", "TimeKey", "UserKey"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Checking for duplicates before inserting
    existing_keys = pd.read_sql(
        "SELECT DateKey, TimeKey, UserKey FROM FactWifiConnection", engine
    )
    fact_wifi_connection = fact_wifi_connection.merge(
        existing_keys, on=["DateKey", "TimeKey", "UserKey"], how="left", indicator=True
    )
    fact_wifi_connection = fact_wifi_connection[
        fact_wifi_connection["_merge"] == "left_only"
    ]
    fact_wifi_connection = fact_wifi_connection.drop(columns="_merge")

    # Insert new rows
    if not fact_wifi_connection.empty:
        fact_wifi_connection.to_sql(
            "FactWifiConnection", engine, if_exists="append", index=False
        )
        print(f"Inserted {len(fact_wifi_connection)} new rows into FactWifiConnection.")
    else:
        print("No new FactWifiConnection rows to insert.")


if __name__ == "__main__":
    main()
