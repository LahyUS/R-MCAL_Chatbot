import sys
sys.path.append('/content/drive/MyDrive/Chatbot/code/MCAL_BOT')

import asyncio
import json
import time
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
import requests
import uvicorn
import nest_asyncio

MAX_CONCURRENCY = 2

semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
global_counter = 0

stop_streaming_requests = []

app = FastAPI()

def generateAnswer(data, key):
    if "question" in data:
        question = data["question"]
        if "history" in data:
          history = data["history"]
        else:
          history = []
        if "path" in data:
          path = data["path"]
        else:
          path = ""

        print("=======PATH:", path)

        qna = QnA()
        final_prompt = qna.generate_prompt(path,question,prompt, history)
        print("+++++++++++++FINAL PROMPT++++++++++++++")
        print(final_prompt)
        print("+++++++++++++++++++++++++++++++++++++++")
        related_question_prompt = qna.generate_related_question_prompt(question, relate_question_prompt, history)
        print("+++++++++++++QUESTION PROMPT++++++++++++++")
        print(related_question_prompt)
        print("+++++++++++++++++++++++++++++++++++++++")

        for reply in chatNew(final_prompt, related_question_prompt, qna.preference):
            if len(stop_streaming_requests) > 0:
                for k in stop_streaming_requests:
                    if k == key:
                        print("========= Stop successss")
                        stop_streaming_requests.remove(k)
                        gc.collect()
                        torch.cuda.empty_cache()
                        return
            data = json.dumps({
                "status":1,
                "answer": reply,
                "key": key
            })
            yield data.encode() + b"\0"

        gc.collect()
        torch.cuda.empty_cache()
        return
    else:
        data = json.dumps({
            "status":0,
            "msg":"Internal model server error"
        })
        yield data.encode() + b"\0"

def release_model_semaphore():
    global semaphore, global_counter
    global_counter -= 1
    semaphore.release()

@app.post('/qna')
async def qna(request: Request):
    global semaphore, global_counter

    global_counter += 1
    print("=============", global_counter)

    data = await request.json()

    # if semaphore is None:
    #     semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    await semaphore.acquire()

    generator = generateAnswer(data, time.time())
    background_tasks = BackgroundTasks()
    background_tasks.add_task(release_model_semaphore)
    return StreamingResponse(generator, background=background_tasks)

@app.post("/getQueueLength")
async def getQueueLength(request: Request):
    global semaphore, global_counter
    data = await request.json()
    if semaphore is None:
        return json.dumps({"status":0})

    inQueue = semaphore._value if semaphore._value is not None else 0
    inWaiting = global_counter - MAX_CONCURRENCY + inQueue
    print(inWaiting, " - ", global_counter, " - ", inQueue)
    return json.dumps({"status":1, "in_queue": inQueue, "in_waiting":inWaiting, "max_concurrency":MAX_CONCURRENCY})

@app.post("/stopStreaming")
async def stopStreaming(request: Request):
    global stop_streaming_requests
    data = await request.json()

    print("----- stop streamine called")

    if "key" in data:
        stop_streaming_requests.append(data["key"])
        return json.dumps({"status":1})
    return json.dumps({"status":0})

@app.post("/uploadDocument")
async def uploadDocument(request: Request):
    print("----- uploadDocument")
    data = await request.json()
    if "path" in data and "data" in data and "file_name" in data:
        qna = QnA()
        qna.save_external_files(data["data"], data["path"], data["file_name"])
        return json.dumps({"status":1})
    return json.dumps({"status":0})

@app.post("/deleteDocument")
async def deleteDocument(request: Request):
    print("----- deleteDocument")
    data = await request.json()
    if "path" in data:
        qna = QnA()
        qna.delete_external_files(data["path"])
        return json.dumps({"status":1})
    return json.dumps({"status":0})


nest_asyncio.apply()
uvicorn.run(app, port=1235)