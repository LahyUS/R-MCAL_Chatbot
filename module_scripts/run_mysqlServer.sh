#!/bin/bash
echo ### run mysqlServer

source venv/bin/activate

cd MCAL_BOT_Chatbot/DBServer

python3 mysqlServer.py
