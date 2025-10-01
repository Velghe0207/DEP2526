from dotenv import load_dotenv
import os
import requests
import pandas as pd
import time

# Loading environment variables from .env file
load_dotenv()  

# Function for POST request to get access token using secret
def get_token(secret: str, url: str = "https://dep.simondg.com/auth/login"):
    response = requests.post(url, json={"secret": secret})
    response.raise_for_status() # Raises an error if the request fails
    return response.json()["access_token"]

# Function for GET request to WiFi API
def get_wifi_clients(token: str, url: str = "https://dep.simondg.com/wifi-clients/last-30-minutes"):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status() # Raises an error if the request fails
    data = response.json()
    return pd.DataFrame(data)

def main():
    # Saving secret in a variable
    secret = os.getenv("SECRET")
    if not secret:
        raise ValueError("SECRET not found in .env file")

    token = get_token(secret)

    # Fetching WiFi clients data and saving to CSV
    df_wifi = get_wifi_clients(token)
    filename = f"data/wifi_clients/wifi_clients_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    df_wifi.to_csv(filename, index=False)


if __name__ == "__main__":
    main()