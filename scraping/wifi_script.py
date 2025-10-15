from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import requests
import pandas as pd
import time

# Loading environment variables from .env file
load_dotenv()

# API functions
def get_token(secret: str, url: str = "https://dep.simondg.com/auth/login"):
    """Function for POST request to get access token using secret"""
    response = requests.post(url, json={"secret": secret})
    response.raise_for_status()  # Raises an error if the request fails
    return response.json()["access_token"]

def get_wifi_clients(token: str, url: str = "https://dep.simondg.com/wifi-clients/last-30-minutes"):
    """Function for GET request to WiFi API"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises an error if the request fails
    data = response.json()
    return pd.DataFrame(data)

# Functions for dataframe processing and writing to datawarehouse
def insert_new_users(df_wifi_edu, engine, df_existing_users):
    """Function for writing new users to DimUser table."""
    df_new_users = df_wifi_edu[["username"]].drop_duplicates()

    # List of existing usernames
    existing_usernames = df_existing_users.tolist()

    # Keep only usernames not in existing_usernames
    not_existing = []
    for username in df_new_users["username"]:
        if username not in existing_usernames:
            not_existing.append(username)

    df_new_users = df_new_users[df_new_users["username"].isin(not_existing)] # Only keep the usernames that are in not_existing
    df_new_users = df_new_users.rename(columns={"username": "UserName"})

    # Write to database if any new users exist
    if not df_new_users.empty:
        df_new_users.to_sql("DimUser", engine, if_exists="append", index=False)
        print(f"Added {len(df_new_users)} new users to DimUser.")
    else:
        print("No new users to add.")

def map_user_keys(df_wifi_edu, engine):
    """Function to map UserKeys to usernames in df_wifi_edu (needed for inserting into FactWifiConnection -> DateKey, TimeKey, UserKey)"""
    df_existing_users = pd.read_sql("SELECT UserKey, UserName FROM DimUser", engine)
    user_keys = []

    # Add UserKey to user_keys if username from df_wifi_edu matches username in df_existing_users
    for username in df_wifi_edu["username"]:
        match = df_existing_users[df_existing_users["UserName"] == username]
        if not match.empty:
            user_keys.append(match.iloc[0]["UserKey"])
        else:
            user_keys.append(None)

    # Now all usernames in df_wifi_edu have a corresponding UserKey
    df_wifi_edu["UserKey"] = user_keys
    return df_wifi_edu

def insert_new_fact_rows(df_wifi_edu, engine):
    """Function for writing wifi connections to FactWifiConnection table"""
    # Keep only the relevant columns and remove duplicates
    fact_wifi_connection = df_wifi_edu[["DateKey", "TimeKey", "UserKey"]].drop_duplicates().reset_index(drop=True)

    # Read existing rows from the database
    existing_keys = pd.read_sql("SELECT DateKey, TimeKey, UserKey FROM FactWifiConnection", engine)

    # Merge to find new rows (those not in existing)
    fact_wifi_connection = fact_wifi_connection.merge(
        existing_keys,
        on=["DateKey", "TimeKey", "UserKey"],
        how="left",
        indicator=True
    )

    # Keep only rows that are in fact_wifi_connection but not in existing_keys
    fact_wifi_connection = fact_wifi_connection[fact_wifi_connection["_merge"] == "left_only"]
    fact_wifi_connection = fact_wifi_connection.drop(columns="_merge")

    # Insert into database if any new rows exist
    if not fact_wifi_connection.empty:
        fact_wifi_connection.to_sql("FactWifiConnection", engine, if_exists="append", index=False)
        print(f"Inserted {len(fact_wifi_connection)} new rows into FactWifiConnection.")
    else:
        print("No new FactWifiConnection rows to insert.")

def main():
    # SQL Server config inside the VM
    server = "127.0.0.1"  
    database = "DEP2_staging"
    username = "sa"
    password = "dep2025-G12"
    driver = "ODBC Driver 18 for SQL Server"

    # SQLAlchemy engine using ODBC
    engine = create_engine(
        f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
    )

    # # SQL Server config local
    # server = "LAPTOP-R1GLLN97"
    # database = "DEP2Test"
    # driver = "ODBC Driver 17 for SQL Server"

    # # Create database-engine
    # engine = create_engine(
    #     f"mssql+pyodbc://@{server}/{database}?trusted_connection=yes&driver={driver}"
    # )

    # Saving secret in a variable
    secret = os.getenv("SECRET")
    if not secret:
        raise ValueError("SECRET not found in .env file")

    token = get_token(secret)

    # Fetching WiFi clients data and filtering for 'eduroam' SSID
    df_wifi = get_wifi_clients(token)
    df_wifi_edu = df_wifi[df_wifi["ssid"] == "eduroam"]

    # Adjust timestamp to +2 hours and round to the nearest minute
    df_wifi_edu["timestamp"] = (
        pd.to_datetime(df_wifi_edu["timestamp"]) + timedelta(hours=2)
    ).dt.round("T")

    # Create DateKey and TimeKey columns
    df_wifi_edu["DateKey"] = df_wifi_edu["timestamp"].dt.strftime("%Y%m%d").astype(int)
    df_wifi_edu["TimeKey"] = df_wifi_edu["timestamp"].dt.strftime("%H%M%S").astype(int)

    # Get existing usernames from DimUser in datawarehouse to make sure we only add new users to DimUser
    df_existing_users = pd.read_sql("SELECT UserName FROM DimUser", engine)["UserName"]

    # Write new users to DimUser
    insert_new_users(df_wifi_edu, engine, df_existing_users)

    # Map UserKeys to usernames in df_wifi_edu, which is needed for FactWifiConnection
    df_wifi_edu = map_user_keys(df_wifi_edu, engine)

    # Write all wifi connections to FactWifiConnection
    insert_new_fact_rows(df_wifi_edu, engine)

if __name__ == "__main__":
    main()
