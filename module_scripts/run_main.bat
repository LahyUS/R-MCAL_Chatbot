@echo off
echo ### run WebChat main

cd venv/Scripts
call activate
echo Current dir: 
cd
cd ../../MCAL_BOT_Chatbot/WebChat
echo Current dir: 
cd
python main.py
