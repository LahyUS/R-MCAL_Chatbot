#!/bin/bash
echo ### Run document server

source venv/bin/activate

cd MCAL_BOT_Chatbot/DBServer

python3 documentServer.py
