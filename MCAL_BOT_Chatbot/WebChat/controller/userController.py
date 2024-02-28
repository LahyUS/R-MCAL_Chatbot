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

    headers = {'Content-Type': 'application/json', 
                "api-key": API_KEY
              }
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                return Status.SUCCESS, response.json()["user_id"], response.json()["token"]

            elif response.json()["status"] == 2:
                print(f"[DEBUG] Login FAIL - Incorrect user id")
                return Status.FAIL, "", "",

            elif response.json()["status"] == 3:
                print(f"[DEBUG] Login FAIL - Duplicate user login")
                return Status.DUPPLICATE_USER, "", ""

    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    
    return Status.ERROR, "", ""


def userLogout(user_id, token):
    url = DATABASE_HOSTNAME + "/logout"
    data = {
        'user_id': user_id
    }
    headers = {
        'Content-Type': 'application/json',
        'api-key': API_KEY,
        'Authorization': f'Bearer {token}'  # Include the user's token in the headers
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            if response.json()["status"] == 1:
                return Status.SUCCESS

            print(f"[DEBUG] Logout FAIL - User is not currently logged in")    
            return Status.FAIL

    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))

    return Status.ERROR
