#!/bin/bash
echo ### Run model server

source venv/bin/activate

cd MCAL_BOT_Chatbot/ModelServer

python3 modelServer.py
