from dotenv import load_dotenv
import os
import requests

# Saving secret in a variable
load_dotenv()  
secret = os.getenv("SECRET")
print(secret)

data = {"secret": secret}

# Saving access token in a variable
def get_token(data, url="https://dep.simondg.com/auth/login"):
    response = requests.post(url, json=data)
    return response.json()["access_token"]

token = get_token(data)
print(token)

# Wifi API
urlWifi = f"https://dep.simondg.com/wifi-clients/last-10-minutes"

# Authentication with access token
headers = {
    "Authorization": f"Bearer {token}",
}

# GET request
response = requests.get(urlWifi, headers=headers)
print(response.json())