import requests
import json
from helper.enumerate import RequestStatus as Status
from helper.enumerate import ChatMode
import re
import aiohttp
import httpx
import time

SESSION = requests.Session()
# MODEL_HOSTNAME = "http://127.0.0.1:1235"
MODEL_HOSTNAME = ""
RESPONSE_TIMEOUT = 1800
with open("../config.json", 'r') as file:
    print("OPEN JSON")
    config = json.load(file)
    if len(config) > 0:
        MODEL_HOSTNAME = config["model_server_address"]
        RESPONSE_TIMEOUT = config["response_timeout"]
        
print(f"[DEBUG] MODEL_HOSTNAME: {MODEL_HOSTNAME}")

def connectToServer(token:str):
    # Create request package to send to server
    url = MODEL_HOSTNAME + '/connect'
    headers = {"Authorization": f"Bearer {token}",
                'Content-Type': 'application/json'}
    print(f"[DEBUG] connectToServer - token: {token}")
    try:
        response = SESSION.post(url, headers=headers)
        #response = SESSION.post(url)
        print("[modelController]++++ response:", response)
        if response.status_code == 200:
            # Request was successful
            data = response.json()
            return data["message"] 
        else:
            print("[modelController]++++ raise_for_status")
            # Request failed, handle the error
            response.raise_for_status()
            return None

    except requests.exceptions.ConnectionError as err:
        print("[modelController]++++ Connection Error:", str(err))
        return None

    except requests.exceptions.RequestException as err:
        # Connection or request error occurred
        print("[modelController]++++ Error occurred when making the connection request:", str(err))
        return None

def disconnecFromServer(token:str):
    # Create request package to send to server
    url = MODEL_HOSTNAME + '/disconnect'
    headers = {"Authorization": f"Bearer {token}",
                'Content-Type': 'application/json'}

    try:
        response = SESSION.post(url, headers=headers)

        if response.status_code == 200:
            # Request was successful
            data = response.json()
            return data["message"] 
        else:
            # Request failed, handle the error
            response.raise_for_status()
            return None

    except requests.exceptions.ConnectionError as err:
        print("[modelController]++++ Connection Error:", str(err))
        return None

    except requests.exceptions.RequestException as err:
        # Connection or request error occurred
        print("[modelController]++++ Error occurred when making the connection request:", str(err))
        return None

def requestAnswerFromModel(token:str, question:str):
    #print("\n\n##########################################################")
    print("[modelController]____ requestAnswerFromModel")
    data = {
        "token" : token,
        "question": question
    }
    url = MODEL_HOSTNAME + '/qna'

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json_data)

    if response.status_code == 200:
        if response.json()["status"] == 1:
            return Status.SUCCESS, response.json()["answer"]
        else:
            return Status.FAIL, "Server has a problem"
    return Status.ERROR, "Internal server error"

def get_openai_answer(question:str):
    url = 'https://api.openai.com/v1/completions'
    headers = {
        'Authorization': 'Bearer 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',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "text-davinci-003",
        "prompt": question,
        "max_tokens": 250,
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    
    print(response)

    if 'answers' in response_json:
        answer = response_json['answers'][0]['text']
        return Status.SUCCESS, answer
    else:
        return Status.ERROR, 'Failed to get an answer.'
    
def get_answer_from_custom_model(question:str):
    url = 'https://d581-35-204-144-140.ngrok-free.app'

    response = requests.get(url+"?question="+question)
    response_json = response.json()
    
    print(response.json())

    if 'response' in response_json:
        answer = response_json['response']
        return Status.SUCCESS, answer
    else:
        return Status.ERROR, 'Failed to get an answer.'

def streamResponse(chatMode:int, token:str, question:str, history=[], path=""):
    #print("\n\n##########################################################")
    print("[modelController]____ streamResponse")
    data = {
        "token" : token,
        "question": question
    }

    if chatMode == ChatMode.GENERAL_CHAT.value:
        knowledge = ""
        print(f"[modelController]____ streamResponse")
        for chat in reversed(history):
            if chat[1] is not None and "You have chosen option **" in chat[1]:
                scope = re.findall(r"\*\*(.*?)\*\*", chat[1])
                scopeKnowledge = scope[0].split(" -> ")
                if len(scopeKnowledge) > 1:
                    chosenOption = scopeKnowledge[1]
                    if len(scopeKnowledge) > 2:
                        for i in range(2, len(scopeKnowledge)):
                            chosenOption += "/" + scopeKnowledge[i]
                    knowledge += chosenOption
                break
        if len(knowledge) == 0:
            path = ""
        else:
            path = knowledge
        data["path"] = "internal/" + path

        if len(history) > 1:
            history = history[:-1]

            history = [item for item in history if 'You have chosen option **' not in item[1]]

    elif chatMode == 2: data["path"] = path

    # Create request package to send to server
    url = MODEL_HOSTNAME + '/qna'
    
    json_data = json.dumps(data)
    print(f"[DEBUG] DATA: {json_data}")
    headers = {"Authorization": f"Bearer {token}",
                'Content-Type': 'application/json'}

    print(f"[DEBUG] streamResponse - token: {token}")
    # Send prepared package to server
    try:
        response = SESSION.post(url, headers=headers, data=json_data, stream=True, timeout=RESPONSE_TIMEOUT)
        print(f"[modelController] response type: {type(response)}---- response: {response}")
        #accumulated_text = ""
        for chunk in response.iter_lines(decode_unicode=False, delimiter=b""):
            try:
                if chunk: 
                    chunk_text = chunk.decode('utf-8')
                    
                    match = re.search(r"data:\s*{([^}]*)}", chunk_text)
                    if match:
                        modified_chunk_text = match.group(1)
                        modified_chunk_text = '{' + modified_chunk_text + '}'
                    else: modified_chunk_text = ""
                    event_data = json.loads(modified_chunk_text)
                    status = event_data.get("status")
                    answer = event_data.get("answer")
                    key = event_data.get("key")
                    
                    if status == 1:
                        yield Status.SUCCESS, answer, key
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from item: {answer} -  Error: {e}")
        return
                                
    except requests.exceptions.ConnectionError as err:
        print("[modelController]++++ Connection Error:", str(err))

    except requests.exceptions.RequestException as err:
        print("[modelController]++++ Error occurred when making the request:", str(err))
    
    print("[modelController]++++ Streanming response has problem")
    yield Status.ERROR, "Server has a problem", 0
   
def getModelServerQueueLength():
    data = {
    }
    
    url = MODEL_HOSTNAME + "/getQueueLength"

    json_data = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    try:
        response = SESSION.post(url, headers=headers, data=json_data)
        response_json = json.loads(response.json())
        print(response_json)
        if response.status_code == 200:
            if int(response_json["status"]) == 1:
                print("Get queue length successfully!")
                return Status.SUCCESS, response_json["in_queue"], response_json["in_waiting"], response_json["max_concurrency"]
            else:
                return Status.FAIL, -1, -1, -1
    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("Error occurred while making the request:", str(err))
    
    print("Get queue length has a problem")
    return Status.ERROR, -1, -1, -1

def stopStreaming(key:str, token:str):
    data = {
        "key":key
    }
    
    url = MODEL_HOSTNAME + "/stopStreaming"

    json_data = json.dumps(data)

    headers = {"Authorization": f"Bearer {token}",
                'Content-Type': 'application/json'}
    try:
        response = SESSION.post(url, headers=headers, data=json_data)
        response_json = response.json()
        if response.status_code == 200:
            if int(response_json["status"]) == 1:
                print("[modelController] Stop streaming successfully!")
                return Status.SUCCESS
            else:
                print("[modelController] Stop streaming Failed!")
                response.raise_for_status()
                return Status.FAIL

    except requests.exceptions.ConnectionError as err:
        print("[modelController] Connection Error:", str(err))
        
    except requests.exceptions.RequestException as err:
        print("[modelController] Error occurred while making the request:", str(err))
    
    print("[modelController] Stop streaming has a problem")
    return Status.ERROR

def uploadDocument(jsonData, path, file_name):
    print("----- modelController uploadDocument")
    data = {
        "path": path,
        "data": jsonData,
        "file_name": file_name
    }
    url = MODEL_HOSTNAME + "/uploadDocument"
    json_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = SESSION.post(url, headers=headers, data=json_data)
        raw_response = response.json()
        status = raw_response['status']
        if response.status_code == 200:
            if int(status) == 1:
                print("[DEBUG] modelController - Upload document successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("[DEBUG] modelController - Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("[DEBUG] modelController - Error occurred while making the request:", str(err))
    
    print("[DEBUG] modelController - Upload document has a problem")
    return Status.ERROR

def deleteDocument(file_path):
    data = {
        "path": file_path
    }
    url = MODEL_HOSTNAME + "/deleteDocument"
    json_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = SESSION.post(url, headers=headers, data=json_data)
        raw_response = response.json()
        status = raw_response['status']

        if response.status_code == 200:
            if int(status) == 1:
                print("[DEBUG] modelController - Delete document successfully!")
                return Status.SUCCESS
            else:
                return Status.FAIL
    except requests.exceptions.ConnectionError as err:
        print("[DEBUG] modelController - Connection Error:", str(err))
    except requests.exceptions.RequestException as err:
        print("[DEBUG] modelController - Error occurred while making the request:", str(err))
    
    print("[DEBUG] modelController - Delete document has a problem")
    return Status.ERROR

# Todo:  Handle user call API model 
        
    
