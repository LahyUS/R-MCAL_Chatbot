import requests
import json
from helper.enumerate import RequestStatus as Status

DATABASE_HOSTNAME = "http://127.0.0.1:1234"
API_KEY = "af84e3cdeaed21a9220fb4fb7a9611de9d1abf85e0642ef50c71076a9fcba150"

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DATABASE_HOSTNAME = config["mysql_server_address"]

print(f"DEBUG DATABASE_HOSTNAME: {DATABASE_HOSTNAME}")
def loadChatHistory(user_id:int, token:str):
    print("[chatController]____ loadChatHistory")
    url = DATABASE_HOSTNAME + '/loadChatHistories'
    data = {
        "user_id": user_id,
        'token': token
    }
    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    
    chatHistoryTitles = []
    chatHistoryTitlesId = []
    chatHistoryTitlesknowledge = []
    chatHistoryContents = {}
    chatHistoryContentsId = {}
    chatHistoryContentsReact = {}
    
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                data = response.json()["data"]
                
                for obj in data:
                    chatHistoryTitles.append(obj["title"])
                    chatHistoryTitlesId.append(obj["title_id"])
                    chatHistoryTitlesknowledge.append(obj["title_knowledge"])
                    chatHistoryContents[obj["title"]] = []
                    chatHistoryContentsId[obj["title"]] = obj["message_id"]
                    chatHistoryContentsReact[obj["title"]] = obj["message_react"]
                    for msg in obj["message"]:
                        chatHistoryContents[obj["title"]].append((msg[0], msg[1]))
                
                return Status.SUCCESS, chatHistoryTitles, chatHistoryTitlesId, chatHistoryTitlesknowledge, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact
            else:
                return Status.SUCCESS, chatHistoryTitles, chatHistoryTitlesId, chatHistoryTitlesknowledge, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact
    except requests.exceptions.ConnectionError as err:
        print("[chatController]++++ Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("[chatController]++++ Error occurred while making the request:", str(err))
    
    return Status.ERROR, chatHistoryTitles, chatHistoryTitlesId, chatHistoryTitlesknowledge, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact

def newTitle(user_id:int, token:str, title:str):
    if isinstance(title, str) and len(title) > 0:
        data = {
            "user_id": user_id,
            "token":token,
            "title": title
        }
        url =  DATABASE_HOSTNAME + '/newTitle'

        json_data = json.dumps(data)

        headers = {'Content-Type': 'application/json', "api-key":API_KEY}
        try:
            response = requests.post(url, headers=headers, data=json_data)

            if response.status_code == 200:
                if response.json()["status"] == 1:
                    print("[Web-Server]____ newTitle: Add new title successfully!")
                    return Status.SUCCESS, response.json()["title_id"]
                else:
                    return Status.FAIL, None
        except requests.exceptions.ConnectionError as err:
            print("Connection Error:", str(err))
        except requests.exceptions.RequestException as err:
            print("Error occurred while making the request:", str(err))
    print("Add new cause a problem!")
    return Status.ERROR, None

def addMessage(user_id:int, token:str, title:str, question:str, answer:str):
    print("[chatController]____ addMessage") 
    data = {
        "user_id": user_id,
        "token":token,
        "title": title,
        "question": question,
        "answer":answer
    }
    #print(f"[DEBUG]____ addMessage - data: {data}")
    url = DATABASE_HOSTNAME + '/newMessage'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("[chatController]++++ Add message successfully!")
                return Status.SUCCESS, response.json()["message_id"]
            else:
                return Status.FAIL, None
                
    except requests.exceptions.ConnectionError as err:
        print("[chatController]++++ Connection Error:", str(err))
    
    except requests.exceptions.RequestException as err:
        print("[chatController]++++ Error occurred while making the request:", str(err))
    
    print("[chatController]++++ Update message has a problem!")
    return Status.ERROR, None

def updateMessage(token:str, message_id:int ,answer:str):
    print("[chatController]____ updateMessage") 
    data = {
        "token":token,
        "message_id": message_id,
        "answer": answer
    }
    url = DATABASE_HOSTNAME + '/updateMessage'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Update message successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    print("Update message has a problem!")
    return Status.ERROR

def voteSubmit(user_id:int, token:str, message_id:int, react:int):
    data = {
        "user_id": user_id,
        "token":token,
        "message_id": message_id,
        "react": react
    }
    url = DATABASE_HOSTNAME + '/submitReact'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Update message react successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    print("Update message react has a problem!")
    return Status.ERROR

def deleteConversation(user_id:int, token:str, titleID):
    data = {
        "user_id": user_id,
        "token": token,
        "title_id": titleID
    }
    url =  DATABASE_HOSTNAME + '/deleteConversation'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Delete conversation successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
        
    print("Delete conversation cause a problem!")
    return Status.ERROR

def updateKnowledge(user_id:int, token:str, title_id, knowledge):
    data = {
        "user_id": user_id,
        "token":token,
        "title_id": title_id,
        "knowledge": knowledge
    }
    url = DATABASE_HOSTNAME + '/updateKnowledge'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Update knowledge title successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))

    print("Update knowledge title has a problem!")
    return Status.ERROR

# File chat mode function

def loadChatHistoryfile(user_id:int, token:str):
    url = DATABASE_HOSTNAME + '/loadChatHistoriesFile'
    data = {
        "user_id": user_id,
        'token': token
    }
    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    
    chatHistoryFiles = []
    chatHistoryFilesId = []
    chatHistoryContents = {}
    chatHistoryContentsId = {}
    chatHistoryContentsReact = {}
    
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                data = response.json()["data"]
                
                for obj in data:
                    chatHistoryFiles.append(obj["file_name"])
                    chatHistoryFilesId.append(obj["file_id"])
                    chatHistoryContents[obj["file_name"]] = []
                    chatHistoryContentsId[obj["file_name"]] = obj["message_id"]
                    chatHistoryContentsReact[obj["file_name"]] = obj["message_react"]
                    for msg in obj["message"]:
                        chatHistoryContents[obj["file_name"]].append((msg[0], msg[1]))
                
                return Status.SUCCESS, chatHistoryFiles, chatHistoryFilesId, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact
            else:
                return Status.SUCCESS, chatHistoryFiles, chatHistoryFilesId, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    
    return Status.ERROR, chatHistoryFiles, chatHistoryFilesId, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact

def newFile(user_id:int, token:str, file_name:str):
    if isinstance(file_name, str) and len(file_name) > 0:
        data = {
            "user_id": user_id,
            "token":token,
            "file_name": file_name
        }
        url =  DATABASE_HOSTNAME + '/newFile'

        json_data = json.dumps(data)

        headers = {'Content-Type': 'application/json', "api-key":API_KEY}
        try:
            response = requests.post(url, headers=headers, data=json_data)

            if response.status_code == 200:
                if response.json()["status"] == 1:
                    print("Add new file successfully!")
                    return Status.SUCCESS, response.json()["file_id"]
                else:
                    return Status.FAIL, None
        except requests.exceptions.ConnectionError as err:
            print("Connection Error:", str(err))
        except requests.exceptions.RequestException as err:
            print("Error occurred while making the request:", str(err))
    print("Add new file cause a problem!")
    return Status.ERROR, None

def addMessageFile(user_id:int, token:str, file_name:str, question:str, answer:str):
    data = {
        "user_id": user_id,
        "token":token,
        "file_name": file_name,
        "question": question,
        "answer":answer
    }
    url = DATABASE_HOSTNAME + '/newMessageFile'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Add message file successfully!")
                return Status.SUCCESS, response.json()["message_id"]
            else:
                return Status.FAIL, None
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    print("Update message file has a problem!")
    return Status.ERROR, None

def updateMessageFile(token:str, message_id ,answer:str):
    data = {
        "token":token,
        "message_id": message_id,
        "answer": answer
    }
    url = DATABASE_HOSTNAME + '/updateMessageFile'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Update message file successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    print("Update message file has a problem!")
    return Status.ERROR

def voteSubmitFile(user_id:int, token:str, message_id, react):
    data = {
        "user_id": user_id,
        "token":token,
        "message_id": message_id,
        "react": react
    }
    url = DATABASE_HOSTNAME + '/submitReactFile'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Update message react file successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    print("Update message react file has a problem!")
    return Status.ERROR

def deleteConversationFile(user_id:int, token:str, fileID):
    data = {
        "user_id": user_id,
        "token":token,
        "file_id": fileID
    }
    url =  DATABASE_HOSTNAME + '/deleteConversationFile'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json', "api-key":API_KEY}
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code == 200:
            if response.json()["status"] == 1:
                print("Delete conversation file successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
        
    print("Delete conversation file cause a problem!")
    return Status.ERROR