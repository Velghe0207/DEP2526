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

    # Generate UserKey
    user_mapping = {
        username: idx + 1
        for idx, username in enumerate(df_wifi_edu["username"].unique())
    }
    df_wifi_edu["UserKey"] = df_wifi_edu["username"].map(user_mapping)

    # Create DimUser table
    dim_user = pd.DataFrame(
        list(user_mapping.items()), columns=["UserName", "UserKey"]
    )[["UserKey", "UserName"]]

    # Create FactWifiConnection table
    fact_wifi_connection = df_wifi_edu[["DateKey", "TimeKey", "UserKey"]]

    # Writing to csv files
    # filename = f"data/wifi_clients/wifi_clients_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    # df_wifi.to_csv(filename, index=False)
    # dim_user.to_csv("DimUser.csv", index=False)
    # fact_wifi_connection.to_csv("FactWifiConnection.csv", index=False)

    # SQL Server configuration on VM or local (change for your own SQL server)
    # server = "127.0.0.1,1500"
    # database = "DEP"
    # username = "SA"
    # password = "Passwordgroep21!"
    # driver = "ODBC Driver 17 for SQL Server"

    # connection with sqlalchemy
    # engine = create_engine(
    #     f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"
    # )

    server = "LAPTOP-R1GLLN97"
    database = "loltest2"
    driver = "ODBC Driver 17 for SQL Server"

    # Creation of database engine
    engine = create_engine(
        f"mssql+pyodbc://@{server}/{database}?trusted_connection=yes&driver={driver}"
    )

    # Writing dataframes to SQL Server
    dim_user.to_sql("DimUser", engine, if_exists="append", index=False)
    fact_wifi_connection.to_sql(
        "FactWifiConnection", engine, if_exists="append", index=False
    )

    print("Dataframe succesvol weggeschreven")


if __name__ == "__main__":
    main()
