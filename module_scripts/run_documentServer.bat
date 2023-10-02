@echo off
echo ### Run document server

cd venv/Scripts
call activate

cd ../../MCAL_BOT_Chatbot/DBServer

python documentServer.py
