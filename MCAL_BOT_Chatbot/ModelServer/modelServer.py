from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import requests
import uvicorn
import json
import time

DATABASE_HOSTNAME = "http://127.0.0.1:1234"
API_KEY = "af84e3cdeaed21a9220fb4fb7a9611de9d1abf85e0642ef50c71076a9fcba150"

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DATABASE_HOSTNAME = config["mysql_server_address"]

app = FastAPI()

def generateData(question):
    result = question + " "
    key = time.time()
    for i in ["Wel", "come ", "to", " ", "Re", "ne", "sas", "sas", "sas", "sas", "sas", "sas", "sas"]:
        result += i
        data = json.dumps({
            "status":1,
            "answer": result,
            "key": key
        })
        yield data.encode() + b"\0"
        time.sleep(0.5)
        
    data = json.dumps({
        "status":1,
        "answer": result + ". Your question: " + question,
        "key":key
    })
    yield data.encode() + b"\0"
    
    
def genTokenFail():
    data = json.dumps({"status":0})
    yield data.encode() + b"\0"
 
@app.post('/qna')
async def qna(request: Request):
    data = await request.json()
    
    if "token" in data:
        url = DATABASE_HOSTNAME + "/checkToken"
        dataSend = {
            'token': data["token"]
        }
        json_data = json.dumps(dataSend)

        headers = {'Content-Type': 'application/json', "api-key":API_KEY}
        try:
            response = requests.post(url, headers=headers, data=json_data)
            
            if response.status_code == 200:
                if response.json()["status"] == 1:
                    question = data['question']
                    if question is not None:
                        return StreamingResponse(generateData(question))
                    
        except requests.exceptions.ConnectionError as err:
            print("Connection Error:", str(err))
        except requests.exceptions.RequestException as err:
            print("Error occurred while making the request:", str(err))
                      
    return StreamingResponse(genTokenFail())


if __name__ == '__main__':
    uvicorn.run(app, port=1235)
