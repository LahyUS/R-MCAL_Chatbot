import requests
import json
from helper.enumerate import RequestStatus as Status

DATABASE_HOSTNAME = "http://127.0.0.1:1234"
API_KEY = "af84e3cdeaed21a9220fb4fb7a9611de9d1abf85e0642ef50c71076a9fcba150"

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DATABASE_HOSTNAME = config["mysql_server_address"]

def userLogin(username:str, password:str):
    url = DATABASE_HOSTNAME + "/login"
    data = {
        'username': username,
        'password': password
    }
    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                return Status.SUCCESS, response.json()["user_id"], response.json()["token"]
            print("Login FAIL")
            return Status.FAIL, "", ""
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    
    return Status.ERROR, "", ""