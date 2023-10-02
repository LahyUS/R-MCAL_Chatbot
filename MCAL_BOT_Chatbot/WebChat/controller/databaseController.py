import requests
import json

DATABASE_HOSTNAME = "http://127.0.0.1:2234"

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DATABASE_HOSTNAME = config["document_server_address"]

def getFolderTree():
    url = DATABASE_HOSTNAME + "/getFolderTree"
    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()["tree"]
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    
    return None