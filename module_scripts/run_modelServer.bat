@echo off
echo ### Run model server

cd venv/Scripts
echo Current dir: 
cd
call activate

cd ../../MCAL_BOT_Chatbot/ModelServer
echo Current dir: 
cd
python modelServer.py
