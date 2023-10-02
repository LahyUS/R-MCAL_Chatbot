@echo off
echo ### run mysqlServer

cd venv/Scripts
echo Current dir: 
cd
call activate

cd ../../MCAL_BOT_Chatbot/DBServer
echo Current dir: 
cd
python mysqlServer.py
