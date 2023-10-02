import gradio as gr
import json
import re
import os
import sys
import shutil
import threading

sys.path.append("..")
from security import authSecurity
from controller import userController , chatController, modelController, databaseController
from helper.enumerate import RequestStatus as Status
from helper.enumerate import ErrorCode
from helper.enumerate import MessageReactCode
from helper.enumerate import StateCode
from helper.enumerate import ChatMode
from helper.enumerate import ChatLimit
from Tools.Autosar2middledatabase import Doc2MiddleData
from Tools.Autosar2middledatabase import getLength

from const_defined import *
from load_threads import * 
from update_threads import *
from generate_threads import *

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DOCUMENT_SERVER_ADDRESS = config["document_server_address"]
        PATH_TO_DATABASE = config["path_to_database"]
        COOKIE_EXPIRE_TIME_SECOND = config["cookie_expire_time_second"]
        MAX_CHAT_IN_CONVERSATION = config["max_number_chat"]
        MAX_CHAT_IN_CONVERSATION_FILE = config["max_number_chat_file_chat_mode"]

def login(username:str, password:str, session:gr.State):
    print("\n\n##########################################################")
    print("[Web-Server]____ login")
    # Check if fields of username and password is empty
    if "token" not in session or "user_id" not in session:
        session = {}
        if len(username) == 0 and len(password) == 0:
            return gr.update(visible=True), gr.update(visible=False), 'Please enter your username and password.', session, "", "START"
        
        # Request login
        status, user_id, token = userController.userLogin(username, password)

        if status == Status.SUCCESS:
            session["token"] = token
            session["user_id"] = user_id
            session["chat_mode"] = ChatMode.GENERAL_CHAT
            tokenDataSession = {
                "user_id": user_id,
                "token":token
            }
            # Encode user info to a token
            tokenSession = authSecurity.create_token(tokenDataSession)
            tokenDataCookie = {
                "token":tokenSession
            }
            # Encode user info token to a token. This token will be saved into cookie
            tokenCookie = authSecurity.create_token(tokenDataCookie)

            return gr.update(visible=False), gr.update(visible=True), "Login successfully!", session, tokenCookie, "START"
        
        elif status == Status.FAIL:
            return gr.update(visible=True), gr.update(visible=False), "Incorrect username or password. Please try again.", session, "", "START"

        else:
            return gr.update(visible=True), gr.update(visible=False), 'Server have problem. Please try again.', session, "", "START"

    return gr.update(visible=False), gr.update(visible=True), "Processing auto login", gr.update(), gr.update(), "", "START"

def logout(session:gr.State):
    disconnectFromModelServer(session)
    return gr.update(visible=True), gr.update(visible=False), "Please enter your username and password.", "", "", {}, "", ""

def connectToModelServer(session:gr.State):
    # Create a connection between the current session and LLM Model Server
    connectResult = modelController.connectToServer(session["token"])
    if connectResult == "Connected":
        print("[Web-Server]++++ Connect to Model Server successfully")
        
    else:
        print("[Web-Server]++++ Connect to Model Server failed")

def disconnectFromModelServer(session:gr.State):
    # Create a connection between the current session and LLM Model Server
    disconnectResult = modelController.disconnecFromServer(session["token"])
    if disconnectResult == "Disconnected":
        print("[Web-Server]++++ Disconnect from Model Server successfully")
        
    else:
        print("[Web-Server]++++ Disconnect from Model Server failed")

def submitQuestion(conversation:list, text:str):
    """
    Update to UI when user submit the question.
    """
    print("\n\n##########################################################")
    print("[Web-Server]____ submitQuestion")
    print("[Web-Server]----", text, " - ", type(text))
    if isinstance(text, str): # check for invalid submission
        conversation = conversation + [(text, None)]
    return conversation, None, gr.update(visible=False)

def errorEventHandler(errorEvent:gr.HTML):
    """
    Handle when errorEvent component change value.
    """
    print("\n\n##########################################################")
    print("[Web-Server]______ errorEventHandler")
    print("[Web-Server]----Error event handler:", errorEvent)
    if errorEvent == ErrorCode.SERVER_FAIL.value:
        return gr.update(visible=True), gr.update(visible=False), 'Internal server error. Please try again.', {}, "", "", "", "", ErrorCode.NONE
    elif errorEvent == ErrorCode.SERVER_ERROR.value:
        return gr.update(visible=True), gr.update(visible=False), 'Server have problem. Please try again.', {}, "", "", "", "", ErrorCode.NONE
    # elif errorEvent == ErrorCode.NO_LOGIN.value:
    #     return gr.update(visible=True), gr.update(visible=False), 'Please enter username and pasword.', {}, "", "", "", "", ErrorCode.NONE
    return (gr.update(),)* 9

def cookTokenCookieDefault(tokenCookieDefault:gr.HTML):
    """
    Remove the last character got from cookie (Do this to get change event of tokenCookieDefault component)
    """
    print("\n\n##########################################################")
    print("[Web-Server]______ cookTokenCookieDefault")
    tokenCookieDefault = tokenCookieDefault[:-1]
    return tokenCookieDefault

def cookLatestTitleCookie(latestTitleCookie:str):
    """
    Remove the last character got from cookie (Do this to get change event of latestTitleCookie component)
    """
    print("\n\n##########################################################")
    print("[Web-Server]______ cookLatestTitleCookie")
    latestTitleCookie = latestTitleCookie[:-1] # Generate new cookie by remove the last char of the current cookie
    return latestTitleCookie

# # Function to get user feedback using a pop-up dialog
# def get_user_feedback():
#     root = tk.Tk()
#     root.withdraw()  # Hide the main window

#     feedback = simpledialog.askstring("User Feedback", "Please provide your feedback:")
#     root.destroy()  # Close the temporary window

#     return feedback

def submitFeedback(Feedback_Box):
    print(f"Feedback_Box: {Feedback_Box}")
    return  gr.update(value=None, interactive=False), gr.update(interactive=False), gr.update(value='Thanks for giving your feedback!', visible=True)

def upvoteSubmit(title:str, file_name:str, conversation:list, session:gr.State, feedback:gr.Textbox, submit_btn:gr.Button):
    """Handle upvote submission."""
    print("\n\n##########################################################")
    print("[Web-Server]______ upvoteSubmit")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        print("[Web-Server]++++ upvoteSubmit")
        if isinstance(title, str) and len(title) > 0:
            if len(conversation) > 0:
                DBConversation = session["content"][title]
                if len(DBConversation) == len(conversation) and len(conversation) == len(session["content_id"][title]):
                    messageID = session["content_id"][title][-1]
                    status = chatController.voteSubmit(session["user_id"], session["token"], messageID, MessageReactCode.UPVOTE.value)
                    if status == Status.SUCCESS:
                        lastchat = (session["content"][title][-1][0], session["content"][title][-1][1] + MSG_NOTIFY_UPVOTE)
                        conversation[-1] = lastchat
                        session["content_react"][title][-1] = MessageReactCode.UPVOTE.value
                        session["content"][title][-1] = lastchat
                        return gr.update(interactive=False), gr.update(interactive=False), session, conversation, gr.update(interactive=True), gr.update(interactive=True)
        print("[Web-Server]++++ Have problem when submit upvote")
    elif "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        print("[Web-Server]++++ upvoteSubmit FILE")
        if isinstance(file_name, str) and len(file_name) > 0:
            if len(conversation) > 0:
                DBConversation = session["content_file"][file_name]
                if len(DBConversation) == len(conversation) and len(conversation) == len(session["content_id_file"][file_name]):
                    messageID = session["content_id_file"][file_name][-1]
                    status = chatController.voteSubmitFile(session["user_id"], session["token"], messageID, MessageReactCode.UPVOTE.value)
                    if status == Status.SUCCESS:
                        lastchat = (session["content_file"][file_name][-1][0], session["content_file"][file_name][-1][1] + MSG_NOTIFY_UPVOTE)
                        conversation[-1] = lastchat
                        session["content_react_file"][file_name][-1] = MessageReactCode.UPVOTE.value
                        session["content_file"][file_name][-1] = lastchat
                        return gr.update(interactive=False), gr.update(interactive=False), session, conversation, gr.update(interactive=True), gr.update(interactive=True)
        print("[Web-Server]++++ Have problem when submit upvote FILE")
    return gr.update(), gr.update(), session, conversation, gr.update(interactive=True), gr.update(interactive=True)

def downvoteSubmit(title:str, file_name:str, conversation:list, session:gr.State):
    """Handle downvote submission."""
    print("\n\n##########################################################")
    print("[Web-Server]______ downvoteSubmit")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        print("[Web-Server]++++ downvoteSubmit")
        if isinstance(title, str) and len(title) > 0:
            if len(conversation) > 0:
                DBConversation = session["content"][title]
                if len(DBConversation) == len(conversation) and len(conversation) == len(session["content_id"][title]):
                    messageID = session["content_id"][title][-1]
                    status = chatController.voteSubmit(session["user_id"], session["token"], messageID, MessageReactCode.DOWNVOTE.value)
                    if status == Status.SUCCESS:
                        lastchat = (session["content"][title][-1][0], session["content"][title][-1][1] + MSG_NOTIFY_DOWNVOTE)
                        conversation[-1] = lastchat
                        session["content_react"][title][-1] = MessageReactCode.DOWNVOTE.value
                        session["content"][title][-1] = lastchat
                        return gr.update(interactive=False),  gr.update(interactive=False), session, conversation, gr.update(interactive=True), gr.update(interactive=True)
        print("[Web-Server]++++ Have problem when submit downvote")

    elif "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        print("[Web-Server]++++ downvoteSubmit FILE")
        if isinstance(file_name, str) and len(file_name) > 0:
            if len(conversation) > 0:
                DBConversation = session["content_file"][file_name]
                if len(DBConversation) == len(conversation) and len(conversation) == len(session["content_id_file"][file_name]):
                    messageID = session["content_id_file"][file_name][-1]
                    status = chatController.voteSubmitFile(session["user_id"], session["token"], messageID, MessageReactCode.DOWNVOTE.value)
                    if status == Status.SUCCESS:
                        lastchat = (session["content_file"][file_name][-1][0], session["content_file"][file_name][-1][1] + MSG_NOTIFY_DOWNVOTE)
                        conversation[-1] = lastchat
                        session["content_react_file"][file_name][-1] = MessageReactCode.DOWNVOTE.value
                        session["content_file"][file_name][-1] = lastchat
                        return gr.update(interactive=False),  gr.update(interactive=False), session, conversation, gr.update(interactive=True), gr.update(interactive=True)
        print("[Web-Server]++++ Have problem when submit downvote FILE")
    return gr.update(), gr.update(), session, conversation, gr.update(interactive=True), gr.update(interactive=True)

def reactiveInput():
    """Enable input component."""
    return gr.update(interactive=True, placeholder="Enter text and press enter"), gr.update(interactive=True)
 
def stopClickhandler(session:gr.State):
    """Hanlde the <Stop generate> button."""
    print("[Web-Server]----- stopClickhandler")
    if "streaming_key" in session and session["streaming_key"] is not None:
        # Request model server stop generate answer
        status = modelController.stopStreaming(session["streaming_key"])
        print("[Web-Server]Call API stop streaming - ", status)
    return "UPDATE", gr.update(interactive=False)

def suggestionSelectHandle(conversation:list, evt: gr.SelectData):
    """Handle user choosing suggested questions"""
    print(f"You selected {evt.value} at {evt.index} from {evt.target}")
    if isinstance(evt.value, str) and len(evt.value) > 0:
        conversation = conversation + [(evt.value, None)]
    print("[Web-Server]-----", " - ", type(conversation))
    return conversation
        
def suggestionDefaultSelectHandle(conversation:list, scopeKnowledge, evt: gr.SelectData):
    """Handle user choosing knowledge suggestion """
    print("[Web-Server]--- suggestionDefaultSelectHandle")
    print(f"You selected {evt.value} at {evt.index} from {evt.target}")

    # Request file server to get the folder tree in database
    documentTree = databaseController.getFolderTree()

    # If choosing the first default, option just append to the chat
    options = []
    if evt.value == defaultOption[0][0]:
        conversation = conversation + [(evt.value, "You have chosen option **" + evt.value + "**. Now you can enter question for creating task list.")]
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=False)

    # If choose the second default suggestion 
    elif evt.value == defaultOption[1][0]:
        conversation = conversation + [(evt.value, "You have chosen option **" + evt.value + "**")]
        scopeKnowledge = [evt.value,]

        for i in documentTree:
            options.append(list(i))

    # The option is not in default options
    else:
        if len(scopeKnowledge) > 0:
            # Handle "go Back" option
            if evt.value == "Go back":
                scopeKnowledge.pop()
                if len(scopeKnowledge) == 1:
                    for i in documentTree:
                        options.append(list(i))
                print("[Web-Server]+++===", scopeKnowledge)
            elif evt.value != "Ok":
                scopeKnowledge.append(evt.value)

            chosenOption = "**" + scopeKnowledge[0]
            subTree = documentTree

            # List folder in an scope choosen by user
            for i in range(1, len(scopeKnowledge)):
                chosenOption += " -> " + scopeKnowledge[i]
                for j in subTree:
                    if scopeKnowledge[i] in j:
                        subTree = j[scopeKnowledge[i]]
                        options = []
                        for k in subTree:
                            options.append(list(k))
                        break

            chosenOption += "**"
            conversation = conversation + [(evt.value, "You have chosen option " + chosenOption)]

    # If knowledge is determined show it to UI
    instruction = ""
    if len(scopeKnowledge) > 1:
        chosenOption = scopeKnowledge[1]
        if len(scopeKnowledge) > 2:
            for i in range(2, len(scopeKnowledge)):
                chosenOption += " -> " + scopeKnowledge[i]
        instruction = "Using knowledge in **" + chosenOption + "** to answer your question."
    
    if len(options) == 0 and len(scopeKnowledge) <= 1:
        options = defaultOption

    # Append "Go Back" and "OK" to options
    if len(scopeKnowledge) > 1:
        options.append(["Go back"])
        options.append(["Ok"])
    
    # Remove chat contain "You have chosen option **" to prevent count with limit number of chat
    tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]
    if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    # Handle choosed option "Ok"
    if evt.value == "Ok":
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    # Update result to UI
    if len(instruction) == 0 and len(options) > 0:
        return conversation, scopeKnowledge, options, gr.update(visible=False)
    elif len(instruction) > 0 and len(options) > 0:
        return conversation, scopeKnowledge, options, gr.update(visible=True, value=instruction)
    elif len(instruction) > 0 and len(options) == 0:
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=False)

def changeToFileChatMode(session:gr.State): 
    session["chat_mode"] = ChatMode.FILE_CHAT
    return (session, ) + (gr.update(visible=False),)*6 + (gr.update(interactive=False),)*8 + (gr.update(visible=True, interactive=True),)*4

def changeToGeneralChatMode(session:gr.State):
    session["chat_mode"] = ChatMode.GENERAL_CHAT
    return (session, ) + (gr.update(visible=True),)*4 + (gr.update(interactive=False),)*8 + (gr.update(visible=False),)*3 + (gr.update(interactive=True),)

def convertFileToJson(file, session:gr.State, progress=gr.Progress(track_tqdm=True)):
    print("[Web-Server]===== convertFileToJson")
    if "file_name" in session and file is not None:
        file_name = session["file_name"][-1]

        index = file_name.find("(")
        if index == -1:
            index = file_name.find(".")
        
        if (index != -1) and (str(file_name[:index].rstrip(' ')) in str(file.name)):
            print("[Web-Server]START convert file")
            num_pages = getLength(file.name)
            for jsonData in progress.tqdm(Doc2MiddleData(file.name), desc="Processing PDf", unit="Pages/" + str(num_pages+1), total=num_pages+1):
                pass
            print("[Web-Server]END convert file")

            print(type(jsonData), " --- ", bool(jsonData))

            if bool(jsonData):
                file_id = session["file_id"][-1]
                path = "external/" + str(file_id) 
                print("[Web-Server]------", file_id, " = ", path)
                status = modelController.uploadDocument(jsonData, path, file_name)
                if status == Status.SUCCESS:
                    print("[Web-Server]==== Upload document to model serer SUCCESS")
        else:
            print("[Web-Server]NOT OKKKKKKKKKK")

    return ""

def createUI():
    generateEvent = []

    textbox_style = '''
    /* Define styles for the custom-textbox class */
    .custom-textbox {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 14px;
    line-height: 1.5;
    transition: border-color 0.2s ease-in-out;
    }

    .custom-textbox:focus {
    border-color: #3498db;
    outline: none;
    }
    '''    
    UI_Theme = gr.Theme.from_hub("gradio/dracula_revamped")
    with gr.Blocks(title="MCAL Bot", theme=UI_Theme, css="#queueHeight {height:60px} #instructionHeight {height:60px} ") as WebChat:
        session = gr.State(value={})
        scopeKnowledge = gr.State(value=[])
        tokenCookieSession = gr.HTML(value="",visible=False)
        tokenCookieDefault = gr.HTML(value="",visible=False)
        setLatestTitleCookie = gr.HTML(value="",visible=False)
        getLatestTitleCookie = gr.HTML(value="",visible=False)
        state = gr.HTML(value=StateCode.NONE ,visible=False)
        
        with gr.Row() as LoginWrap:
            with gr.Column(scale=0.35):
                gr.Row(visible=False)
            with gr.Column(scale=0.3):
                gr.Markdown("# Login")
                username = gr.Textbox(label="Username", placeholder="Type your username")
                password = gr.Textbox(type="password", label="Password", placeholder="Type your password")
                loginBtn = gr.Button("Submit")
                loginNotify = gr.HTML("Please enter your username and password.")
            with gr.Column(scale=0.35):
                gr.Row(visible=False)
        with gr.Row(visible=False) as MainWrap:
            with gr.Column():
                with gr.Row() as MenuBarWrap:
                    with gr.Column(scale=0.7):
                        gr.Row(visible=False)
                    with gr.Column(scale=0.1, min_width=0):
                        fileChatBtn = gr.Button("File chat")
                    with gr.Column(scale=0.1, min_width=0):
                        generalChatButton = gr.Button("General chat", interactive=False)
                    with gr.Column(scale=0.1, min_width=0):
                        LogoutBtn = gr.Button("Logout")
                with gr.Row() as ChatWrap:
                    with gr.Column(scale=0.2):
                        with gr.Row():
                            newchatBtn = gr.Button("New chat")
                        with gr.Row():
                            newFileBtn = gr.Button("Upload new file", visible = False)
                        with gr.Row():
                            queueLength = 0
                            waitingLength = 0
                            max_concurrency = 0
                            def doGetQueueLength():
                                nonlocal queueLength, waitingLength, max_concurrency
                                status, inQueue, inWaiting, maxConcurrency = Status.FAIL, 0,0,0 #modelController.getModelServerQueueLength()
                                if status == Status.SUCCESS:
                                    max_concurrency = maxConcurrency
                                    queueLength = max_concurrency - inQueue
                                    waitingLength = inWaiting
                                else:
                                    queueLength = -1
                                    waitingLength = -1
                                    max_concurrency = -1
                            def updateQueueLengthUI():
                                nonlocal queueLength, waitingLength, max_concurrency
                                output = ""
                                if queueLength == -1 or waitingLength == -1 or max_concurrency == -1:
                                    output += "<br>Queue: CANNOT connect to server"
                                else:
                                    output += "<br>Serving: " + str(queueLength) + "/" + str(max_concurrency) #+ "<br>Waiting: " + str(waitingLength)
                                return output
                            getQueueLength = gr.HTML(value=doGetQueueLength, visible=False, every=2)
                            modelServerQueue = gr.HTML(value="", elem_id="queueHeight")
                            modelServerQueue.change(updateQueueLengthUI, [], [modelServerQueue], every=2)
            
                        with gr.Row():
                            chatHistoryList = gr.Dropdown(label="Chat history")
                        with gr.Row():
                            fileHistoryList = gr.Dropdown(label="Files Uploaded", visible=False)
                    with gr.Column(scale=0.8):
                        with gr.Row():
                            knowledge = gr.Markdown(value="", visible=False)
                        with gr.Row():
                            suggestionDefault = gr.Dataframe(headers=["You can choose following below options to continue"],datatype=["str"],label=None, wrap=True, value=[], visible=False, max_rows=1)
                        with gr.Row():
                            ChatBot = gr.Chatbot([], elem_id="chatbot").style(height=450)
                        with gr.Row():
                            fileUpload = gr.File(file_types=["text", ".pdf", ".docx"], visible=False)
                        with gr.Row():    
                            suggestion = gr.Dataframe(headers=["Suggestion:"],datatype=["str"],label=None, wrap=True, value=[["Hello"], ["Hi"]], visible=False)
                        with gr.Row():
                            with gr.Column(scale=0.9):
                                InputText = gr.Textbox(
                                    show_label=False,
                                    placeholder="Enter question",
                                ).style(container=False)
                            with gr.Column(scale=0.1, min_width=0):
                                SendBtn = gr.Button("Send")
                        with gr.Row() as button_row:
                            stop_btn = gr.Button(value="⏹️  Stop Generation")
                            regenerate_btn = gr.Button(value="🔄  Regenerate")
                            clear_btn = gr.Button(value="🗑️  Clear conversation")
                        with gr.Box(visible=True):
                            with gr.Row():
                                upvote_btn = gr.Button(value="👍  Upvote")
                                downvote_btn = gr.Button(value="👎  Downvote")
                            with gr.Row(variant="compact", visible=True):
                                with gr.Column(scale=0.9):
                                    Feedback_Box = gr.Textbox(
                                        show_label=False,
                                        info="Write your correct answer",
                                        interactive=False,
                                        lines=5,
                                        max_lines=50,
                                        #elem_id="Feedback",
                                        #elem_classes=textbox_style
                                        ).style(container=True)
                                    #Feedback_Box.blur()
                                with gr.Column(scale=0.1, min_width=0):
                                    Send_Feedback_Btn = gr.Button("Submit", interactive=False)

                        with gr.Row():
                            with gr.Column(scale=1.0):
                                Feedback_Result = gr.Textbox(
                                    show_label=False,
                                    placeholder="",
                                    interactive=False,
                                    visible=False,
                                    ).style(container=False)

        # Event Gradio custom
        errorEvent = gr.HTML(value=ErrorCode.NONE,visible=False)
        stopEvent = gr.HTML(value="",visible=False)
                            
        # Event handlers
        generateEvent.append(InputText.submit(submitQuestion, [ChatBot, InputText], [ChatBot, InputText, Feedback_Result]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList, session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion, suggestionDefault]))
        
        generateEvent.append(SendBtn.click(submitQuestion, [ChatBot, InputText], [ChatBot, InputText, Feedback_Result]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList, session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion, suggestionDefault]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion, suggestionDefault]))
        
        password.submit(login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession,modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken).then(
            fn=connectToModelServer, inputs=[session], outputs=[])
        
        loginBtn.click(login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession, modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken).then(
            fn=connectToModelServer, inputs=[session], outputs=[])
            
        LogoutBtn.click(logout, [session], [LoginWrap, MainWrap, loginNotify, username, password, session, getLatestTitleCookie, tokenCookieSession]).then(
            fn=None, inputs=None, outputs=None, _js=deleteAccessToken)

        # Add event that runs as soon as the demo loads in the browser
        WebChat.load(fn=cookTokenCookieDefault, inputs=[tokenCookieDefault], outputs=[tokenCookieDefault], _js=getAccessToken) 
        
        chatHistoryList.change(loadConversationFromSession, [chatHistoryList, session, ChatBot], [chatHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, clear_btn, regenerate_btn, SendBtn, InputText, knowledge, suggestionDefault, suggestion]).then(
            updateLatestTitleToCookie, inputs=[chatHistoryList, session], outputs=[setLatestTitleCookie]).then(
            fn=None, inputs=[setLatestTitleCookie], outputs=None, _js=setLastestTitleToken)
        
        newchatBtn.click(addNewConversation, [], [ChatBot, chatHistoryList, upvote_btn, downvote_btn, clear_btn, regenerate_btn, stop_btn, SendBtn, InputText, suggestion, suggestionDefault], queue=False)
        
        tokenCookieDefault.change(updateUserIDFromCookie, inputs=[tokenCookieDefault, session], outputs=[session], queue=True).then(
            login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession,modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken)
            
        getLatestTitleCookie.change(loadLatestConversation, inputs=[getLatestTitleCookie, session], outputs=[chatHistoryList, getLatestTitleCookie, ChatBot, upvote_btn, downvote_btn, clear_btn, regenerate_btn, stop_btn, suggestionDefault, knowledge])
        
        tokenCookieSession.change(fn=None, inputs=[tokenCookieSession], outputs=None, _js=setAccessToken)
        
        upvote_btn.click(upvoteSubmit, [chatHistoryList, fileHistoryList, ChatBot, session, Feedback_Box, Send_Feedback_Btn], [downvote_btn, upvote_btn, session, ChatBot, Feedback_Box, Send_Feedback_Btn])
        downvote_btn.click(downvoteSubmit, [chatHistoryList, fileHistoryList, ChatBot, session, Feedback_Box, Send_Feedback_Btn], [upvote_btn, downvote_btn, session, ChatBot, Feedback_Box, Send_Feedback_Btn])
        Feedback_Box.submit(submitFeedback, [Feedback_Box], [Feedback_Box, Send_Feedback_Btn, Feedback_Result])
        Send_Feedback_Btn.click(submitFeedback, [Feedback_Box], [Feedback_Box, Send_Feedback_Btn, Feedback_Result])
        Feedback_Box.blur(None, [], [])

        clear_btn.click(deleteConversation, [chatHistoryList, session], [chatHistoryList, ChatBot, session, upvote_btn, downvote_btn, clear_btn,regenerate_btn, stop_btn, SendBtn, InputText, suggestionDefault]).then(
            deleteConversationFile, [fileHistoryList, session], [fileHistoryList, ChatBot, session, upvote_btn, downvote_btn, clear_btn,regenerate_btn, stop_btn, SendBtn, InputText, fileUpload])
        
        generateEvent.append(regenerate_btn.click(regenerateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault], queue=True).then(
            regenerateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault], queue=True))
        
        stop_btn.click(fn=stopClickhandler, inputs=[session], outputs=[stopEvent, stop_btn])
            
        #jsEndEvent = "window.addEventListener('beforeunload', function() { gradioInterface.invokeFunction('disconnect_on_close'); });"
        #generateEvent.append(fn=disconnectFromModelServer, inputs=[session["token"]], outputs=[], _js=jsEndEvent)

        # stopEvent.change(stopEventHandler, [stopEvent, chatHistoryList, ChatBot, session, state], [session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, stopEvent], cancels=generateEvent)
        
        errorEvent.change(errorEventHandler, [errorEvent], [LoginWrap, MainWrap, loginNotify, session, username, password, getLatestTitleCookie, tokenCookieSession, errorEvent])
        
        suggestion.select(suggestionSelectHandle, [ChatBot], [ChatBot]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion, suggestionDefault])
        
        suggestionDefault.select(suggestionDefaultSelectHandle, [ChatBot, scopeKnowledge], [ChatBot, scopeKnowledge, suggestionDefault, knowledge]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            updateConversationDefault, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn, clear_btn, regenerate_btn, stop_btn, state, suggestion])
        
        fileChatBtn.click(changeToFileChatMode, [session], [session, newchatBtn, chatHistoryList, suggestionDefault, suggestion, knowledge, ChatBot,  upvote_btn, downvote_btn,clear_btn,regenerate_btn, stop_btn, InputText, SendBtn, fileChatBtn, fileHistoryList, fileUpload, generalChatButton, newFileBtn]).then(
            loadFileList, [session], [fileHistoryList])

        generalChatButton.click(changeToGeneralChatMode, [session], [session, newchatBtn, chatHistoryList, knowledge, ChatBot,  upvote_btn, downvote_btn, clear_btn, regenerate_btn, stop_btn, InputText, SendBtn, generalChatButton , fileHistoryList, fileUpload, newFileBtn, fileChatBtn]). then(
            loadConversationFromSession, [chatHistoryList, session, ChatBot], [chatHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, clear_btn,regenerate_btn, SendBtn, InputText, knowledge, suggestionDefault, suggestion])

        fileUpload.change(fileUploadChange, [fileUpload, session], [fileUpload, session, fileHistoryList, ChatBot]).then(
            convertFileToJson,[fileUpload, session],[InputText]).then(
            initilizeConversationFile, [fileUpload, session, fileHistoryList], [ChatBot, fileUpload, upvote_btn, downvote_btn, stop_btn, regenerate_btn, clear_btn, InputText, SendBtn])
        
        fileHistoryList.change(loadConversationFileFromSession, [fileHistoryList, session, ChatBot], [fileHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, regenerate_btn, clear_btn, SendBtn, InputText, suggestion, fileUpload])

        newFileBtn.click(uploadNewFile, [], [fileHistoryList, upvote_btn, downvote_btn, stop_btn, clear_btn,regenerate_btn, SendBtn, InputText, ChatBot, fileUpload, suggestion])

        # Register the disconnectFromModelServer function with the close attribute of the WebChat app
        def on_close():
            disconnectFromModelServer(session)

        WebChat.close(on_close)
    
    return WebChat

if __name__ == "__main__":
    webchat = createUI()
    webchat.queue(concurrency_count=3) 
    webchat.launch(share=True, max_threads=50, auth_message="Please login to use the service", inbrowser=False, server_name='172.29.155.77', server_port=1027)