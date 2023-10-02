import gradio as gr
import json
import re
import os
import sys
import shutil

sys.path.append("..")
from security import authSecurity
from controller import userController , chatController, modelController, databaseController
from helper.enumerate import RequestStatus as Status
from helper.enumerate import ErrorCode
from helper.enumerate import MessageReactCode
from helper.enumerate import StateCode
from helper.enumerate import ChatMode
from Tools.Autosar2middledatabase import Doc2MiddleData
from Tools.Autosar2middledatabase import getLength

DOCUMENT_SERVER_ADDRESS = "http://127.0.0.1:2234/"
PATH_TO_DATABASE = ""
COOKIE_EXPIRE_TIME_SECOND = 60
MAX_CHAT_IN_CONVERSATION = 15
MAX_CHAT_IN_CONVERSATION_FILE = 15

with open("../config.json", 'r') as file:
    config = json.load(file)
    if len(config) > 0:
        DOCUMENT_SERVER_ADDRESS = config["document_server_address"]
        PATH_TO_DATABASE = config["path_to_database"]
        COOKIE_EXPIRE_TIME_SECOND = config["cookie_expire_time_second"]
        MAX_CHAT_IN_CONVERSATION = config["max_number_chat"]
        MAX_CHAT_IN_CONVERSATION_FILE = config["max_number_chat_file_chat_mode"]

MSG_NOTIFY_UPVOTE = """<br><br>  <span style="color: green;">**👍 Upvoted**</span>"""
MSG_NOTIFY_DOWNVOTE = """<br><br>  <span style="color: red;">**👎 Downvoted**</span>"""
MSG_NOTIFY_REACHED_TO_CHAT_LIMIT = """<br><span></span><br>  <span style="color: orange;">**You have reached the chat limit in this conversation - """ + str(MAX_CHAT_IN_CONVERSATION) + """ messages**</span>"""
MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM = """<span style="color:red">**Error:** Model server has problem.</span>"""

setAccessToken = """(token) => {
                    const d = new Date();
                    d.setTime(d.getTime() + (""" + str(COOKIE_EXPIRE_TIME_SECOND) + """ * 1000));
                    let expires = "expires="+d.toUTCString();
                    if(typeof token === 'string' && token.trim() !== ''){
                        document.cookie = "authorization="+token+ ";" + expires + ";path=/"; 
                    }
                }"""
            
setLastestTitleToken = """(token) => {
                    if(typeof token === 'string' && token.trim() !== ''){
                        console.log("set title kkkkkkkk");
                        document.cookie = "lastTitle="+token+ ";path=/"; 
                    }
                }"""
                
getAccessToken = """() => {
                    let name = "authorization" + "=";
                    let ca = document.cookie.split(';');
                    let result="";
                    for(let i = 0; i < ca.length; i++) {
                        let c = ca[i];
                        while (c.charAt(0) == ' ') {
                            c = c.substring(1);
                        }
                        if (c.indexOf(name) == 0) {
                            return c.substring(name.length, c.length) + "E";
                        }
                    }
                    return ""
                }"""
                
getLatestTitleToken = """() => {
                    console.log("getLatestTitleToken---");
                    let name = "lastTitle" + "=";
                    let ca = document.cookie.split(';');
                    let result="";
                    for(let i = 0; i < ca.length; i++) {
                        let c = ca[i];
                        while (c.charAt(0) == ' ') {
                            c = c.substring(1);
                        }
                        if (c.indexOf(name) == 0) {
                            console.log("OK");
                            return c.substring(name.length, c.length) + "E";
                        }
                    }
                    return ""
                }"""
                
deleteAccessToken = """() => {
                    document.cookie = "authorization" + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                }"""
                
defaultOption = [["Create task list"], ["Ask for information about the document"]]
            
def updateUserIDFromCookie(tokenCookieDefault, session):
    if isinstance(tokenCookieDefault, str) and len(tokenCookieDefault) > 0:
        tokenSession = authSecurity.get_current_token(tokenCookieDefault)
        if len(tokenSession) > 0:
            user_id, token = authSecurity.decodeToken(tokenSession)
            session["token"] = token
            session["user_id"] = user_id
            session["chat_mode"] = ChatMode.GENERAL_CHAT
    return session

def login(username, password, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ login")
    if "token" not in session or "user_id" not in session:
        session = {}
        if len(username) == 0 and len(password) == 0:
            return gr.update(visible=True), gr.update(visible=False), 'Please enter your username and password.', session, "", "START"
        
        status, user_id, token = userController.userLogin(username, password)

        if status == Status.SUCCESS:
            session["token"] = token
            session["user_id"] = user_id
            session["chat_mode"] = ChatMode.GENERAL_CHAT
            tokenDataSession = {
                "user_id": user_id,
                "token":token
            }
            tokenSession = authSecurity.create_token(tokenDataSession)
            tokenDataCookie = {
                "token":tokenSession
            }
            tokenCookie = authSecurity.create_token(tokenDataCookie)
            return gr.update(visible=False), gr.update(visible=True), "Login successfully!", session, tokenCookie, "START"
        elif status == Status.FAIL:
            return gr.update(visible=True), gr.update(visible=False), "Incorrect username or password. Please try again.", session, "", "START"
        else:
            return gr.update(visible=True), gr.update(visible=False), 'Server have problem. Please try again.', session, "", "START"
    return gr.update(visible=False), gr.update(visible=True), "Processing auto login", gr.update(), gr.update(), "", "START"

def logout(session):
    return gr.update(visible=True), gr.update(visible=False), "Please enter your username and password.", "", "", {}, "", ""

def loadHistoryChat(session):
    print("\n\n##########################################################")
    print("[Web-Server]____ loadHistoryChat")
    if isinstance(session, dict) and "token" in session and "user_id" in session:
        status, chatHistoryTitles, chatHistoryTitlesId, chatHistoryTitlesknowledge, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact = chatController.loadChatHistory(session["user_id"], session["token"])
        if status == Status.SUCCESS:
            print(f"[Web-Server] loadHistoryChat is SUCCESS")
            if len(chatHistoryContentsReact) > 0 and len(chatHistoryContents) > 0 and len(chatHistoryTitles) > 0:
                for i in range(len(chatHistoryTitles)):
                    title = chatHistoryTitles[i]
                    for j in range(len(chatHistoryContentsReact[title])):
                        react = chatHistoryContentsReact[title][j]
                        if react is not None and react != 0:
                            answer = chatHistoryContents[title][j][-1]
                            if react == MessageReactCode.UPVOTE.value:
                                answer += MSG_NOTIFY_UPVOTE
                            if react == MessageReactCode.DOWNVOTE.value:
                                answer += MSG_NOTIFY_DOWNVOTE
                            chatHistoryContents[title][j] = (chatHistoryContents[title][j][0], answer)
            
            session["title"] = chatHistoryTitles
            session["title_id"] = chatHistoryTitlesId
            session["title_knowledge"] = chatHistoryTitlesknowledge
            session["content"] = chatHistoryContents
            session["content_id"] = chatHistoryContentsId
            session["content_react"] = chatHistoryContentsReact
            return gr.update(choices=chatHistoryTitles, value=""), gr.update(value=None), session, ErrorCode.NONE
        elif status == Status.FAIL:
            return gr.update(choices=None, value=None), gr.update(value=None), {}, ErrorCode.SERVER_FAIL
        elif status == Status.ERROR:
            return gr.update(choices=None, value=None), gr.update(value=None), {}, ErrorCode.SERVER_ERROR
        
    return gr.update(choices=None, value=None), gr.update(value=None), {}, ErrorCode.NO_LOGIN

def loadConversationFromSession(title, session, conversation):
    print("\n\n##########################################################")
    print("[Web-Server]____ loadConversationFromSession")
    if isinstance(session, dict) and "content" in session:
        print("[Web-Server]++++ exist contentttt")
        chatHistoryTitles = session["title"]
        chatHistoryContents = session["content"]
        reacts = session["content_react"] # store the content of the user's input
        if title in chatHistoryContents:
            notifyMarkdown = MSG_NOTIFY_REACHED_TO_CHAT_LIMIT
            history = chatHistoryContents[title]

            if(conversation != history): # BUGGGGG: converted_history = [[conversation[0], conversation[1]]]
                print("[Web-Server] DEBUG conversation")
                updateOptions = (gr.update(visible=False),) * 2
            else:
                updateOptions = (gr.update(),) * 2

            knowledge = ""
            for chat in reversed(history):
                if chat[1] is not None and "You have chosen option **" in chat[1]:
                    scope = re.findall(r"\*\*(.*?)\*\*", chat[1])
                    scopeKnowledge = scope[0].split(" -> ")
                    if len(scopeKnowledge) > 1:
                        chosenOption = scopeKnowledge[1]
                        if len(scopeKnowledge) > 2:
                            for i in range(2, len(scopeKnowledge)):
                                chosenOption += " -> " + scopeKnowledge[i]
                        knowledge += ("Using knowledge in **" + chosenOption + "** to answer your question.")
                    break
            
            if len(knowledge) == 0:
                updateKnowledge = gr.update(visible=False)
            else:
                updateKnowledge = gr.update(visible=True, value=knowledge)
            if history is not None:
                tmpHistory = [item for item in history if item[1] is not None and 'You have chosen option **' not in item[1]]

            print("[Web-Server]---- last char react:", reacts[title][-1])

            if len(tmpHistory) < MAX_CHAT_IN_CONVERSATION:
                if isinstance(history[-1][1],str) and history[-1][1].find(notifyMarkdown) > 0:
                    history[-1] = (history[-1][0], history[-1][1].replace(notifyMarkdown, ""))
                if title in reacts:
                    if len(reacts[title]) > 0 and isinstance(reacts[title][-1], int) and reacts[title][-1] > 0:
                        print("[Web-Server][DEBUG] if 11 ===")
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 4 + (updateKnowledge,) + updateOptions
                    else:
                        print("[Web-Server][DEBUG] if 12 ===")
                        session["content"][title] = [("", "")]
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 4 + (updateKnowledge,) + updateOptions
            else:
                if isinstance(history[-1][1],str) and history[-1][1].find(notifyMarkdown) < 0:
                    history[-1] = (history[-1][0], history[-1][1] + notifyMarkdown)
                
                if title in reacts:
                    if len(reacts[title]) > 0 and isinstance(reacts[title][-1], int) and reacts[title][-1] > 0:
                        print("[Web-Server][DEBUG] if 21 ===")
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
                    else:
                        print("[Web-Server][DEBUG] if 22 ===")
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
                print("[Web-Server][DEBUG] if 23 ===")
                return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
    print("[Web-Server][DEBUG] Default ===")
    return (gr.update(value=None), gr.update(value=None),) +  (gr.update(),) * 7 + (gr.update(visible=False),) + (gr.update(),)*2

def addNewConversation():
    defaultOption = [["Create task list"], ["Ask for information about the document"]]
    instuction = "You can choose following below options to continue"
    return ([], gr.update(value=None),) + (gr.update(interactive=False),)*5 + (gr.update(interactive=True),)*2 + (gr.update(visible=False),) + (gr.update(visible=True,  value=defaultOption),)+ (gr.update(visible=True,  value=instuction),)

def submitQuestion(conversation , text):
    print("\n\n##########################################################")
    print("[Web-Server]____ submitQuestion")
    print("[Web-Server]----", text, " - ", type(text))
    if isinstance(text, str) and len(text) > 0:
        conversation = conversation + [(text, None)]
    print(f"[Web-Server]++++ conversation: {conversation}")
    return conversation, None

def updateLatestTitleToCookie(title, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ updateLatestTitleToCookie")
    if "title" in session:
        if title in session["title"]  or ((title == None or title == "") and len(session["title"]) > 0):  
            print("[Web-Server]lasttitle----- ", title)
            tokenData = {
                "title":title
            }
            return authSecurity.create_token(tokenData)

    return ""

def loadLatestConversation(latestTitleCookie, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ loadLatestConversation", latestTitleCookie)
    if len(latestTitleCookie) > 0:
        latestTitle = authSecurity.get_latest_title(latestTitleCookie)
        if len(latestTitle) > 0:
            if "title" in session and latestTitle in session["title"] and "content" in session:
                history = session["content"][latestTitle] 
                knowledge = ""

                for chat in reversed(history):
                    if chat[1] is not None and "You have chosen option **" in chat[1]:
                        scope = re.findall(r"\*\*(.*?)\*\*", chat[1])
                        scopeKnowledge = scope[0].split(" -> ")
                        if len(scopeKnowledge) > 1:
                            chosenOption = scopeKnowledge[1]
                            if len(scopeKnowledge) > 2:
                                for i in range(2, len(scopeKnowledge)):
                                    chosenOption += " -> " + scopeKnowledge[i]
                            knowledge += ("Using knowledge in **" + chosenOption + "** to answer your question.")
                        break
                
                if len(knowledge) == 0:
                    updateKnowledge = gr.update(visible=False)
                else:
                    updateKnowledge = gr.update(visible=True, value=knowledge)

                return (gr.update(choices=session["title"], value=latestTitle), "", session["content"][latestTitle],) + (gr.update(interactive=True),) * 4 + (gr.update(interactive=False),) + (gr.update(visible=False),) + (updateKnowledge,) 
    print("[Web-Server]++++ Invalid lastest title")

    return (gr.update(), "", gr.update()) + (gr.update(interactive=False),) * 5+ (gr.update(visible=True,  value=defaultOption),)+ (gr.update(visible=False),)

def updateChatHistoryList(title, conversation, session):
    print("[Web-Server]______ updateChatHistoryList")

    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        if title is not None and len(title) > 0:
            return title, session

        elif len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str) and len(conversation[-1][0]) > 0:
            title = conversation[-1][0]
            
            if len(title) > 50:
                title = title[:50]
            if "title" in session:
                chatHistoryTitles = session["title"]
            else:
                chatHistoryTitles = []
                
            count = 1
            while title in chatHistoryTitles:
                start_index = title.rfind("(")
                end_index = title.rfind(")")
                if start_index != -1 and end_index != -1 and start_index < end_index and len(title) - end_index <= 1:
                    tmp = title[start_index + 1: end_index]
                    try:
                        count = int(tmp)
                        title = title[:start_index] + f"({count + 1})"
                    except ValueError:
                        title += " (1)"
                else:
                    title += " (1)"

            print("[Web-Server]---- title: ", title)
                
            status, titleID = chatController.newTitle(session["user_id"], session["token"], title)
            if status == Status.SUCCESS:
                chatHistoryTitles.append(title)
                session["title"] = chatHistoryTitles
                
                if "title_id" in session:
                    chatHistoryTitlesID = session["title_id"]
                else:
                    chatHistoryTitlesID = []
                chatHistoryTitlesID.append(titleID)
                session["title_id"] = chatHistoryTitlesID
                
                if "content" in session:
                    chatHistoryContents = session["content"]
                else:
                    chatHistoryContents = {}
                chatHistoryContents[title] = conversation
                
                session["content"] = chatHistoryContents
                session["content_id"][title] = []
                session["content_react"][title] = []
                
                return gr.update(choices=chatHistoryTitles, value=title), session
    return gr.update(), session

def extractRelatedQuestion(data):
    print("\n\n##########################################################")
    print("[Web-Server]______ extractRelatedQuestion")
    result = []
    i = data.find("**Related question:**")
    if i != -1:
        i += len(str("**Related question:**")) + 1
        while i < len(data):
            tempString = ""
            while i < len(data) and data[i] != '\n':
                tempString += data[i]
                i += 1
            if len(tempString) > 0:
                tempString = re.sub(r'^[^a-zA-Z]+', '', tempString)
                if len(tempString) > 0 and tempString[-1] == '\n':
                    tempString = tempString[:-1]
                result.append([tempString,])
            if i < len(data) and data[i] == '\n':
                i += 1
    return result
            
def extractLinkReference(data):
    print("\n\n##########################################################")
    print("[Web-Server]______ extractLinkReference")

    result = "<br><br>**Reference documents:**\n"
    i = data.find("**Reference documents:**")
    end_i = data.find("<br>.")
    if i != -1:
        i += len(str("**Reference documents:**")) + 1
        while i < end_i:
            tempString = ""
            while i < end_i and data[i] != '\n':
                tempString += data[i]
                i += 1
            if len(tempString) > 0:
                tempString = re.sub(r'^[^a-zA-Z]+', '', tempString)
                if len(tempString) > 0 and tempString[-1] == '\n':
                    tempString = tempString[:-1]
                
                page_index = tempString.find("|")
                if page_index != -1:
                    page_index == int(page_index)
                    page = tempString[page_index:]
                    tempString = tempString[:page_index]
                else:
                    page = ""

                if "external" in tempString:
                    pdf_files = [file for file in os.listdir(PATH_TO_DATABASE + tempString) if file.lower().endswith('.pdf')]
                    if len(pdf_files) > 0:
                        displayString = pdf_files
                        tempString += "/" + pdf_files[0]
                else:
                    tempString = "internal/" + tempString

                print("[Web-Server]========= tempstring", tempString)

                displayString = tempString
                if "internal/" in displayString:
                    displayString = displayString.replace("internal/", "")
                if "external/" in displayString:
                    displayString = displayString.replace("external/", "")
                
                result += "- " + '<a href="' + DOCUMENT_SERVER_ADDRESS + "files/" + tempString.replace("/", "!") + '" target="_blank">' + displayString + '</a>  .Page ' + page + '\n'
            if i < end_i and data[i] == '\n':
                i += 1
    return result

def generateAnswer(title, conversation, session):
    print("\n\n##########################################################")
    print("[Web-Server]______ generateAnswer")
    print(f"[DEBUG]---- conversation: {conversation}")

    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        if len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str):
            question = conversation[-1][0]
        else:
            question = ""
            
        print("[Web-Server]---- question: ", question)
        
        if "content" in session:
            chatHistoryContents = session["content"]
        else:
            chatHistoryContents = {}
        
        if isinstance(question, str) and len(question) > 0 and (conversation[-1][1] == None or len(conversation[-1][1]) <= 0):

            print("[Web-Server]++++ start request answer")

            answer = ""
            print(f"[DEBUG]____ handled conversation")
            print(f"[DEBUG]---- conversation: {conversation}")

            for status, ans, key in modelController.streamResponse(1, session["token"], question, conversation):
                print(f"[Web-Server]++++ answer: ", ans)
                print(f"[Web-Server]++++ status: ", status)
                if status == Status.SUCCESS:
                    print(f"[Web-Server]++++ status: ", status)
                    session["streaming_key"] = key

                    referLinkPos = ans.find("**Reference documents:**")
                    endReferLinkString = "<br>."
                    endReferLink = ans.find(endReferLinkString)
                    if referLinkPos != -1 and endReferLink != -1:
                        referLink = extractLinkReference(ans[referLinkPos:])
                        ans = ans[:referLinkPos] + referLink + ans[endReferLink + len(endReferLinkString):]

                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1][1] = ans[:relatedQuestionPos]
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[title] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    else:
                        conversation[-1][1] = ans
                        answer = ans
                        chatHistoryContents[title] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                elif status == Status.FAIL or status == Status.ERROR:
                    print(f"[Web-Server]++++ status: ", status)
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    # chatHistoryContents[title] = conversation
                    # session["content"] = chatHistoryContents
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return

            #print(f"[Web-Server]++++ answer: ", ans)
            print(f"[Web-Server]++++ status: ", status)

            status, msgID = chatController.addMessage(session["user_id"], session["token"], title, question, answer)
            if status == Status.SUCCESS:
                session["content_id"][title].append(msgID)
                session["content"] = chatHistoryContents
                session["content_react"][title].append(None)
                session["streaming_key"] = None

                tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]

                if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
                    if isinstance(conversation[-1][1],str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            else:
                print("[Web-Server]++++ Update message FAIL")
                
        elif isinstance(question, str) and len(question) <= 0:
            conversation = conversation[:-1]
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        print("[Web-Server]++++ End generate answer")
        return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def generateAnswerFile(file_name, conversation, session):
    print("\n\n##########################################################")
    print("[Web-Server]______ generateAnswerFILE")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        if conversation is not None and len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str):
            question = conversation[-1][0]
        else:
            question = ""
            
        print("[Web-Server]---- question: ", question)
        
        if "content_file" in session:
            chatHistoryContents = session["content_file"]
        else:
            chatHistoryContents = {}
        
        if isinstance(question, str) and len(question) > 0 and (conversation[-1][1] == None or len(conversation[-1][1]) <= 0):
            print("[Web-Server]++++ start request answer")

            index = session["file_name"].index(file_name)
            fileID = session["file_id"][index]
            path = "external/" + str(fileID)

            answer = ""
            for status, ans, key in modelController.streamResponse(2, session["token"], question, conversation, path):
                print(f"[Web-Server]---- ans: {ans}")
                if status == Status.SUCCESS:
                    session["streaming_key"] = key

                    referLinkPos = ans.find("**Reference documents:**")
                    endReferLinkString = "<br>."
                    endReferLink = ans.find(endReferLinkString)
                    if referLinkPos != -1 and endReferLink != -1:
                        referLink = extractLinkReference(ans[referLinkPos:])
                        ans = ans[:referLinkPos] + referLink + ans[endReferLink + len(endReferLinkString):]

                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1][1] = ans[:relatedQuestionPos]
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[file_name] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    else:
                        conversation[-1][1] = ans
                        answer = ans
                        chatHistoryContents[file_name] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                elif status == Status.FAIL or status == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    # chatHistoryContents[title] = conversation
                    # session["content"] = chatHistoryContents
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
            #print(answer)
            status, msgID = chatController.addMessageFile(session["user_id"], session["token"], file_name, question, answer)
            if status == Status.SUCCESS:
                session["content_id_file"][file_name].append(msgID)
                session["content_file"] = chatHistoryContents
                session["content_react_file"][file_name].append(None)
                session["streaming_key"] = None

                if len(conversation) >= MAX_CHAT_IN_CONVERSATION_FILE:
                    if isinstance(conversation[-1][1],str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            else:
                print("[Web-Server]++++ Update message FAIL")
                
        elif isinstance(question, str) and len(question) <= 0 and len(conversation) > 0:
            conversation = conversation[:-1]
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        print("[Web-Server].++++ End generate answer")
        return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def doCookieLoginhandle(doCookieLogin, session, tokenCookie):
    print("\n\n##########################################################")
    print("[Web-Server]______ doCookieLoginhandle")
    if isinstance(doCookieLogin, str) and doCookieLogin == "LOGIN":
        if "token" in session and "user_id" in session:
            return gr.update(visible=False), gr.update(visible=True), "Login successfully!", session, tokenCookie, ""
    return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    
def errorEventHandler(errorEvent):
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

def cookTokenCookieDefault(tokenCookieDefault):
    print("\n\n##########################################################")
    print("[Web-Server]______ cookTokenCookieDefault")
    tokenCookieDefault = tokenCookieDefault[:-1]
    return tokenCookieDefault

def cookLatestTitleCookie(latestTitleCookie):
    print("\n\n##########################################################")
    print("[Web-Server]______ cookLatestTitleCookie")
    latestTitleCookie = latestTitleCookie[:-1]
    return latestTitleCookie

def upvoteSubmit(title, file_name, conversation, session):
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
                        return gr.update(interactive=False), gr.update(interactive=False), session, conversation
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
                        return gr.update(interactive=False), gr.update(interactive=False), session, conversation
        print("[Web-Server]++++ Have problem when submit upvote FILE")
    return gr.update(), gr.update(), session, conversation

def downvoteSubmit(title, file_name, conversation, session):
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
                        return gr.update(interactive=False),  gr.update(interactive=False), session, conversation
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
                        return gr.update(interactive=False),  gr.update(interactive=False), session, conversation
        print("[Web-Server]++++ Have problem when submit downvote FILE")
    return gr.update(), gr.update(), session, conversation

def reactiveInput():
    return gr.update(interactive=True, placeholder="Enter text and press enter"), gr.update(interactive=True)

def deleteConversation(title, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ deleteConversation")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        if isinstance(title, str) and len(title) > 0 and "title" in session and "title_id" in session:
            try:
                index = session["title"].index(title)
                titleID = session["title_id"][index]
                
                status = chatController.deleteConversation(session["user_id"], session["token"], titleID)
                if status == Status.SUCCESS:
                    print("[Web-Server]delete success ----")
                    del session["title"][index]
                    del session["title_id"][index]
                    return (gr.update(value = "", choices=session["title"]), [], session) + (gr.update(interactive=False),)*5 + (gr.update(interactive=True),)*2 + (gr.update(visible=True, value=defaultOption),)
                
            except ValueError:
                print("[Web-Server]Delete conversation FAIL")
        return (gr.update(), gr.update(), session) + (gr.update(interactive=False),)*5 + (gr.update(interactive=True),)*2 + (gr.update(visible=False),)
    else:
        return (gr.update(), gr.update(), session) + (gr.update(),)*8
    
def deleteConversationFile(file_name, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ deleteConversationFile")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        if isinstance(file_name, str) and len(file_name) > 0 and "file_name" in session and "file_name" in session:
            try:
                index = session["file_name"].index(file_name)
                fileID = session["file_id"][index]
                
                status = chatController.deleteConversationFile(session["user_id"], session["token"], fileID)
                if status == Status.SUCCESS:
                    path = "external/" + str(fileID)
                    status = modelController.deleteDocument(path)
                    if status == Status.SUCCESS:
                        print("[Web-Server]===== Delete file to server SUCCESS")

                    print("[Web-Server]delete FILE success ----")
                    del session["file_name"][index]
                    del session["file_id"][index]
                    return (gr.update(value = "", choices=session["file_name"]), gr.update(visible=False, value=[]), session) + (gr.update(interactive=False),)*7 + (gr.update(visible=True),)
                
            except ValueError:
                print("[Web-Server]Delete FILE conversation FAIL")
        return (gr.update(), gr.update(), session) + (gr.update(interactive=False),)*7 + (gr.update(),)
    else:
        return (gr.update(), gr.update(), session) + (gr.update(),)*8

def regenerateAnswer(title, conversation, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ regenerateAnswer")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        if len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str):
            question = conversation[-1][0]
        else:
            question = ""
            
        print("[Web-Server]---- question: ", question)
        
        if "content" in session:
            chatHistoryContents = session["content"]
        else:
            chatHistoryContents = {}
        
        if isinstance(question, str) and len(question) > 0:
            answer = ""
            for status, ans, key in modelController.streamResponse(1, session["token"], question, conversation):
    
                if status == Status.SUCCESS:
                    session["streaming_key"] = key

                    referLinkPos = ans.find("**Reference documents:**")
                    endReferLinkString = "<br>."
                    endReferLink = ans.find(endReferLinkString)
                    if referLinkPos != -1 and endReferLink != -1:
                        referLink = extractLinkReference(ans[referLinkPos:])
                        ans = ans[:referLinkPos] + referLink + ans[endReferLink + len(endReferLinkString):]

                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1] = (conversation[-1][0], ans[:relatedQuestionPos])
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[title] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    else:
                        conversation[-1] = (conversation[-1][0], ans)
                        answer = ans
                        chatHistoryContents[title] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                elif status == Status.FAIL or status == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    # chatHistoryContents[title] = conversation
                    # session["content"] = chatHistoryContents
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
            #print(answer)
            status= chatController.updateMessage(session["token"], session["content_id"][title][-1], answer)
            if status == Status.SUCCESS:
                session["content"] = chatHistoryContents
                session["content_react"][title][-1] = 0
                session["streaming_key"] = None

                tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]

                if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
                    if isinstance(conversation[-1][1],str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            else:
                print("[Web-Server]++++ Update message FAIL")
                
        elif isinstance(question, str) and len(question) <= 0:
            conversation = conversation[:-1]
        
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def regenerateAnswerFile(file_name, conversation, session):
    print("\n\n##########################################################")
    print("[Web-Server]____ regenerateAnswerFile")
    if "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        if conversation is not None and len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str):
            question = conversation[-1][0]
        else:
            question = ""
            
        print("[Web-Server]---- question: ", question)
        
        if "content_file" in session:
            chatHistoryContents = session["content_file"]
        else:
            chatHistoryContents = {}
        
        if isinstance(question, str) and len(question) > 0:
            print("[Web-Server]++++ start request answer")

            index = session["file_name"].index(file_name)
            fileID = session["file_id"][index]
            path = "external/" + str(fileID)

            answer = ""
            for status, ans, key in modelController.streamResponse(2, session["token"], question, conversation, path):
                print("[Web-Server]---- ans: ", ans)
                if status == Status.SUCCESS:
                    session["streaming_key"] = key

                    referLinkPos = ans.find("**Reference documents:**")
                    endReferLinkString = "<br>."
                    endReferLink = ans.find(endReferLinkString)
                    if referLinkPos != -1 and endReferLink != -1:
                        referLink = extractLinkReference(ans[referLinkPos:])
                        ans = ans[:referLinkPos] + referLink + ans[endReferLink + len(endReferLinkString):]

                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1][1] = ans[:relatedQuestionPos]
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[file_name] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    else:
                        conversation[-1][1] = ans
                        answer = ans
                        chatHistoryContents[file_name] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                elif status == Status.FAIL or status == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    # chatHistoryContents[title] = conversation
                    # session["content"] = chatHistoryContents
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
            #print(answer)
            status = chatController.updateMessageFile(session["token"], session["content_id_file"][file_name][-1], answer)
            if status == Status.SUCCESS:
                session["content_file"] = chatHistoryContents
                session["content_react_file"][file_name][-1] = 0
                session["streaming_key"] = None

                if len(conversation) >= MAX_CHAT_IN_CONVERSATION_FILE:
                    if isinstance(conversation[-1][1],str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            else:
                print("[Web-Server]++++ Update message FAIL")
                
        elif isinstance(question, str) and len(question) <= 0:
            conversation = conversation[:-1]
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        print("[Web-Server]++++ End generate answer")
        return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def stopClickhandler(session):
    print("[Web-Server]----- stopClickhandler")
    if "streaming_key" in session and session["streaming_key"] is not None:
        status = modelController.stopStreaming(session["streaming_key"])
        print("[Web-Server]Call API stop streaming - ", status)
    return "UPDATE", gr.update(interactive=False)

def stopEventHandler(stopEvent, title, conversation, session, state):
    print("[Web-Server]stop testttttttt")
    if stopEvent == "UPDATE":
        print("[Web-Server]---stop event")
        
        if len(title) > 0 and len(conversation) > 0:
            if "content" in session:
                chatHistoryContents = session["content"]
            else:
                chatHistoryContents = {}
            
            if state == StateCode.GENERATING.value:
                if len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str):
                    question = conversation[-1][0]
                    answer = conversation[-1][1]
                    chatHistoryContents[title] = conversation
                    status, msgID = chatController.addMessage(session["user_id"], session["token"], title, question, answer)
                    if status == Status.SUCCESS:
                        session["content_id"][title].append(msgID)
                        session["content"] = chatHistoryContents
                        session["content_react"][title].append(None)
                        print("[Web-Server]okkkkk9999999999")
                        return (session, ) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + ("",)
                    
            elif state == StateCode.REGENERATING.value:
                chatHistoryContents[title] = conversation
                session["content"] = chatHistoryContents
                session["content_react"][title][-1] = 0
                print("[Web-Server]OKkkkkkk88888888888")
                return (session, ) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + ("",)
        print("[Web-Server]Stop event have error ---")
    print("[Web-Server]FAILllllllllllllllll")
    return (session, ) + (gr.update(),) * 7 + (StateCode.NONE,) + ("",)

def suggestionSelectHandle(conversation, evt: gr.SelectData):
    print(f"You selected {evt.value} at {evt.index} from {evt.target}")
    if isinstance(evt.value, str) and len(evt.value) > 0:
        conversation = conversation + [(evt.value, None)]
    print("[Web-Server]-----", " - ", type(conversation))
    return conversation
        
def suggestionDefaultSelectHandle(conversation, scopeKnowledge, evt: gr.SelectData):
    print("[Web-Server]--- suggestionDefaultSelectHandle")

    print(f"You selected {evt.value} at {evt.index} from {evt.target}")

    documentTree = databaseController.getFolderTree()

    options = []
    if evt.value == defaultOption[0][0]:
        conversation = conversation + [(evt.value, "You have chosen option **" + evt.value + "**. Now you can enter question for creating task list.")]
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=False)

    elif evt.value == defaultOption[1][0]:
        conversation = conversation + [(evt.value, "You have chosen option **" + evt.value + "**")]
        scopeKnowledge = [evt.value,]

        for i in documentTree:
            options.append(list(i))

    else:
        if len(scopeKnowledge) > 0:
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

    instruction = ""
    if len(scopeKnowledge) > 1:
        chosenOption = scopeKnowledge[1]
        if len(scopeKnowledge) > 2:
            for i in range(2, len(scopeKnowledge)):
                chosenOption += " -> " + scopeKnowledge[i]
        instruction = "Using knowledge in **" + chosenOption + "** to answer your question."
    
    if len(options) == 0 and len(scopeKnowledge) <= 1:
        options = defaultOption

    if len(scopeKnowledge) > 1:
        options.append(["Go back"])
        options.append(["Ok"])
    
    tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]
    if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    if evt.value == "Ok":
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    if len(instruction) == 0 and len(options) > 0:
        return conversation, scopeKnowledge, options, gr.update(visible=False)
    elif len(instruction) > 0 and len(options) > 0:
        return conversation, scopeKnowledge, options, gr.update(visible=True, value=instruction)
    elif len(instruction) > 0 and len(options) == 0:
        return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=True, value=instruction)

    return conversation, scopeKnowledge, gr.update(visible=False), gr.update(visible=False)

def updateConversationDefault(title, conversation, session):
    print("[Web-Server]+++ updateConversationDefault")

    if len(conversation[-1][0]) > 0 and conversation[-1][0] != "Ok":
        if "content" in session:
            chatHistoryContents = session["content"]
        else:
            chatHistoryContents = {}
        status, msgID = chatController.addMessage(session["user_id"], session["token"], title, conversation[-1][0], conversation[-1][1])
        if status == Status.SUCCESS:
            chatHistoryContents[title] = conversation
            session["content_id"][title].append(msgID)
            session["content"] = chatHistoryContents
            session["content_react"][title].append(None)
            session["streaming_key"] = None
            print("[Web-Server]updateConversationDefault SUCCESSSS")
            tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]
            if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
                if isinstance(conversation[-1][1],str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                    conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),) * 2
                return
            yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),) * 2
            return
    else:
        if conversation[-1][0] == "Ok":
            conversation.pop()
        print("[Web-Server]Update message FAIL")
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),) * 2
        return

def changeToFileChatMode(session): 
    session["chat_mode"] = ChatMode.FILE_CHAT
    return (session, ) + (gr.update(visible=False),)*6 + (gr.update(interactive=False),)*8 + (gr.update(visible=True, interactive=True),)*4

def changeToGeneralChatMode(session):
    session["chat_mode"] = ChatMode.GENERAL_CHAT
    return (session, ) + (gr.update(visible=True),)*4 + (gr.update(interactive=False),)*8 + (gr.update(visible=False),)*3 + (gr.update(interactive=True),)

def loadHistoryChatFile(session):
    print("[Web-Server]+++ loadHistoryChat FILE")
    if isinstance(session, dict) and "token" in session and "user_id" in session:
        status, chatHistoryFiles, chatHistoryFilesId, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact = chatController.loadChatHistoryfile(session["user_id"], session["token"])
        if status == Status.SUCCESS:
            print(f"[Web-Server] loadHistoryChatFile is SUCCESS")
            if len(chatHistoryContentsReact) > 0 and len(chatHistoryContents) > 0 and len(chatHistoryFiles) > 0:
                for i in range(len(chatHistoryFiles)):
                    file_name = chatHistoryFiles[i]
                    for j in range(len(chatHistoryContentsReact[file_name])):
                        react = chatHistoryContentsReact[file_name][j]
                        if react is not None and react != 0:
                            answer = chatHistoryContents[file_name][j][-1]
                            if react == MessageReactCode.UPVOTE.value:
                                answer += MSG_NOTIFY_UPVOTE
                            if react == MessageReactCode.DOWNVOTE.value:
                                answer += MSG_NOTIFY_DOWNVOTE
                            chatHistoryContents[file_name][j] = (chatHistoryContents[file_name][j][0], answer)
            
            session["file_name"] = chatHistoryFiles
            session["file_id"] = chatHistoryFilesId
            session["content_file"] = chatHistoryContents
            session["content_id_file"] = chatHistoryContentsId
            session["content_react_file"] = chatHistoryContentsReact
            return session, ErrorCode.NONE
        elif status == Status.FAIL:
            return {}, ErrorCode.SERVER_FAIL
        elif status == Status.ERROR:
            return {}, ErrorCode.SERVER_ERROR
        
    return {}, ErrorCode.NO_LOGIN

def loadFileList(session):
    print("[Web-Server]-----load File list")
    if "file_name" in session:
        chatHistoryFiles = session["file_name"]
        return gr.update(value=None, choices=chatHistoryFiles)
    return gr.update()

def loadConversationFileFromSession(file_name, session, conversation):
    print("[Web-Server]--- load Conversation FILE From Session---")
    print("[Web-Server]--- file_name:", file_name)
    if isinstance(session, dict) and "content_file" in session:
        print("[Web-Server]exist file contentttt")
        chatHistoryFiles = session["file_name"]
        chatHistoryContents = session["content_file"]
        reacts = session["content_react_file"]
        if file_name in chatHistoryContents:
            notifyMarkdown = MSG_NOTIFY_REACHED_TO_CHAT_LIMIT
            history = chatHistoryContents[file_name]

            if len(history) < MAX_CHAT_IN_CONVERSATION_FILE:
                print("[Web-Server]if 1")
                if isinstance(history[-1][1],str) and history[-1][1].find(notifyMarkdown) > 0:
                    history[-1] = (history[-1][0], history[-1][1].replace(notifyMarkdown, ""))
                if file_name in reacts:
                    if (len(reacts[file_name]) > 0 and isinstance(reacts[file_name][-1], int) and reacts[file_name][-1] > 0):
                        print("[Web-Server]if 11 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 4 + (gr.update(visible=False),)*2
                    elif len(history) <= 1:
                        print("[Web-Server]if 12 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=False),) * 4 + (gr.update(interactive=True),) * 3 + (gr.update(visible=False),)*2
                    else:
                        print("[Web-Server]if 13 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 4 + (gr.update(visible=False),)*2
            else:
                print("[Web-Server]if 2")
                if isinstance(history[-1][1],str) and history[-1][1].find(notifyMarkdown) < 0:
                    history[-1] = (history[-1][0], history[-1][1] + notifyMarkdown)
                
                if file_name in reacts:
                    if (len(reacts[file_name]) > 0 and isinstance(reacts[file_name][-1], int) and reacts[file_name][-1] > 0):
                        print("[Web-Server]if 21 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2  + (gr.update(visible=False),)*2
                    elif len(history) <= 1:
                        print("[Web-Server]if 22 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=False),) * 4 + (gr.update(interactive=True),) * 3  + (gr.update(visible=False),)*2
                    else:
                        print("[Web-Server]if 23 ===")
                        return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2  + (gr.update(visible=False),)*2
                print("[Web-Server]if 23 ===")
                return (gr.update(value=file_name, choices=chatHistoryFiles), gr.update(value=history, visible=True),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2  + (gr.update(visible=False),)*2
    print("[Web-Server]Default ===")
    return (gr.update(), gr.update(value=None),) +  (gr.update(),) * 9

def fileUploadChange(file, session):
    print("[Web-Server]--- FILE CHANGE")
    if file is not None:
        file_name = os.path.basename(file.name)
        if len(file_name) > 0:
            if len(file_name) > 50:
                file_name = file_name[:50]
            
            if "file_name" in session:
                chatHistoryFiles = session["file_name"]
            else:
                chatHistoryFiles = []
                
            count = 1
            while file_name in chatHistoryFiles:
                start_index = file_name.rfind("(")
                end_index = file_name.rfind(")")
                dot_index = file_name.rfind(".")
                if start_index != -1 and end_index != -1 and start_index < end_index and dot_index != -1 and end_index < dot_index:
                    tmp = file_name[start_index + 1: end_index]
                    try:
                        count = int(tmp)
                        file_name = file_name[:start_index] + f"({count + 1})" + file_name[dot_index:]
                    except ValueError:
                        file_name = file_name[:start_index] + " (1)" + file_name[dot_index:]
                else:
                    file_name = file_name[:dot_index] + " (1)" + file_name[dot_index:]

            print("[Web-Server]----", file_name, " - ", chatHistoryFiles)

            if len(file_name) > 0:
                print("[Web-Server]--------==", session["user_id"], session["token"], file_name)
                status, file_id = chatController.newFile(session["user_id"], session["token"], file_name)
                if status == Status.SUCCESS:

                    destination = PATH_TO_DATABASE + "external/" + str(file_id) + "/"
                    if not os.path.exists(destination):
                        os.makedirs(destination)
                    
                    destination += os.path.basename(file.name)
                    print("[Web-Server]---Destination file copy", destination)
                    shutil.copy(file.name, destination) # copy file name to external document storage
                    
                    chatHistoryFiles.append(file_name)
                    session["file_name"] = chatHistoryFiles
                    
                    if "file_id" in session:
                        chatHistoryFilesID = session["file_id"]
                    else:
                        chatHistoryFilesID = []
                    chatHistoryFilesID.append(file_id)
                    session["file_id"] = chatHistoryFilesID
                    
                    session["content_id_file"][file_name] = []
                    session["content_react_file"][file_name] = []

                    print("[Web-Server]----- UPDATE", file_name, chatHistoryFiles)

                    return gr.update(visible=False), session, gr.update(value=file_name, choices=chatHistoryFiles), gr.update(visible=True, value=[])
                
    print("[Web-Server]=== default")
    return (gr.update(),) * 4

def convertFileToJson(file, session, progress=gr.Progress(track_tqdm=True)):
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

def initilizeConversationFile(file, session, file_name):
    print("[Web-Server]-------initilizeConversationFile")
    if file is not None:
        conversation = []
        conversation.append((os.path.basename(file.name), "You have uploaded **" + os.path.basename(file.name) + "**. Now you can ask anything about the document."))
        if "content_file" in session:
            chatHistoryContents = session["content_file"]
        else:
            chatHistoryContents = {}
        chatHistoryContents[file_name] = conversation

        print("[Web-Server]=====", session["user_id"], session["token"], file_name, conversation[-1][0], conversation[-1][1])

        status, msgID = chatController.addMessageFile(session["user_id"], session["token"], file_name, conversation[-1][0], conversation[-1][1])
        print("[Web-Server]++++==== addMessageFile STATUS:", status)
        if status == Status.SUCCESS:
            session["content_id_file"][file_name].append(msgID)
            session["content_file"] = chatHistoryContents
            session["content_react_file"][file_name].append(None)
            return (conversation, None) + (gr.update(interactive=False),)*4 + (gr.update(interactive=True),)*3
    return (gr.update(), )*9

def uploadNewFile():
    print("---- uploadNewFile")
    return (gr.update(value=None),) + (gr.update(interactive=False),)*7 + (gr.update(visible=False),) + (gr.update(visible=True, value=None),) + (gr.update(visible=False),) 

def createUI():
    generateEvent = []
    
    # UI Create
    with gr.Blocks(title="MCAL Bot", css="#queueHeight {height:60px} #instructionHeight {height:60px} ") as WebChat:
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
                                    placeholder="Enter text and press enter",
                                ).style(container=False)
                            with gr.Column(scale=0.1, min_width=0):
                                SendBtn = gr.Button("Send")
                        with gr.Row() as button_row:
                            upvote_btn = gr.Button(value="👍  Upvote")
                            downvote_btn = gr.Button(value="👎  Downvote")
                            stop_btn = gr.Button(value="⏹️  Stop Generation")
                            regenerate_btn = gr.Button(value="🔄  Regenerate")
                            clear_btn = gr.Button(value="🗑️  Clear conversation")
                            
        # Event Gradio custom
        errorEvent = gr.HTML(value=ErrorCode.NONE,visible=False)
        stopEvent = gr.HTML(value="",visible=False)
                            
        # Event handlers
        generateEvent.append(InputText.submit(submitQuestion, [ChatBot, InputText], [ChatBot, InputText]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault]))
        
        generateEvent.append(SendBtn.click(submitQuestion, [ChatBot, InputText], [ChatBot, InputText]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault]))
        
        password.submit(login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession,modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken)
        
        loginBtn.click(login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession,modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken)
            
        LogoutBtn.click(logout, [session], [LoginWrap, MainWrap, loginNotify, username, password, session, getLatestTitleCookie, tokenCookieSession]).then(
            fn=None, inputs=None, outputs=None, _js=deleteAccessToken)
        
        WebChat.load(fn=cookTokenCookieDefault, inputs=[tokenCookieDefault], outputs=[tokenCookieDefault], _js=getAccessToken)
        
        chatHistoryList.change(loadConversationFromSession, [chatHistoryList, session, ChatBot], [chatHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, clear_btn,regenerate_btn, SendBtn, InputText, knowledge, suggestionDefault, suggestion]).then(
            updateLatestTitleToCookie, inputs=[chatHistoryList, session], outputs=[setLatestTitleCookie]).then(
            fn=None, inputs=[setLatestTitleCookie], outputs=None, _js=setLastestTitleToken)
        
        newchatBtn.click(addNewConversation, [], [ChatBot, chatHistoryList, upvote_btn, downvote_btn, clear_btn,regenerate_btn, stop_btn, SendBtn, InputText, suggestion, suggestionDefault], queue=False)
        
        tokenCookieDefault.change(updateUserIDFromCookie, inputs=[tokenCookieDefault, session], outputs=[session], queue=True).then(
            login, [username, password, session], [LoginWrap, MainWrap, loginNotify, session, tokenCookieSession,modelServerQueue]).then(
            loadHistoryChat, [session], [chatHistoryList, ChatBot, session, errorEvent]).then(
            loadHistoryChatFile, [session], [session, errorEvent]).then(
            fn=cookLatestTitleCookie, inputs=[getLatestTitleCookie], outputs=[getLatestTitleCookie], _js=getLatestTitleToken)
            
        getLatestTitleCookie.change(loadLatestConversation, inputs=[getLatestTitleCookie, session], outputs=[chatHistoryList, getLatestTitleCookie, ChatBot, upvote_btn, downvote_btn,clear_btn,regenerate_btn, stop_btn, suggestionDefault, knowledge])
        
        tokenCookieSession.change(fn=None, inputs=[tokenCookieSession], outputs=None, _js=setAccessToken)
        
        upvote_btn.click(upvoteSubmit, [chatHistoryList, fileHistoryList,ChatBot, session], [downvote_btn, upvote_btn, session, ChatBot])
        
        downvote_btn.click(downvoteSubmit, [chatHistoryList, fileHistoryList,ChatBot, session], [upvote_btn, downvote_btn, session, ChatBot])
        
        clear_btn.click(deleteConversation, [chatHistoryList, session], [chatHistoryList, ChatBot, session, upvote_btn, downvote_btn, clear_btn,regenerate_btn, stop_btn, SendBtn, InputText, suggestionDefault]).then(
            deleteConversationFile, [fileHistoryList, session], [fileHistoryList, ChatBot, session, upvote_btn, downvote_btn, clear_btn,regenerate_btn, stop_btn, SendBtn, InputText, fileUpload])
        
        generateEvent.append(regenerate_btn.click(regenerateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault], queue=True).then(
            regenerateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault], queue=True))
        
        stop_btn.click(fn=stopClickhandler, inputs=[session], outputs=[stopEvent, stop_btn])
            
        # stopEvent.change(stopEventHandler, [stopEvent, chatHistoryList, ChatBot, session, state], [session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, stopEvent], cancels=generateEvent)
        
        errorEvent.change(errorEventHandler, [errorEvent], [LoginWrap, MainWrap, loginNotify, session, username, password, getLatestTitleCookie, tokenCookieSession, errorEvent])
        
        suggestion.select(suggestionSelectHandle, [ChatBot], [ChatBot]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            generateAnswer, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion]).then(
            generateAnswerFile, [fileHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion, suggestionDefault])
        
        suggestionDefault.select(suggestionDefaultSelectHandle, [ChatBot, scopeKnowledge], [ChatBot, scopeKnowledge, suggestionDefault, knowledge]).then(
            updateChatHistoryList, [chatHistoryList, ChatBot, session], [chatHistoryList,session]).then(
            updateConversationDefault, [chatHistoryList, ChatBot, session], [ChatBot, session, upvote_btn, downvote_btn, InputText, SendBtn,clear_btn,regenerate_btn, stop_btn, state, suggestion])
        
        fileChatBtn.click(changeToFileChatMode, [session], [session, newchatBtn, chatHistoryList, suggestionDefault, suggestion, knowledge, ChatBot,  upvote_btn, downvote_btn,clear_btn,regenerate_btn, stop_btn, InputText, SendBtn, fileChatBtn, fileHistoryList, fileUpload, generalChatButton, newFileBtn]).then(
            loadFileList, [session], [fileHistoryList])

        generalChatButton.click(changeToGeneralChatMode, [session], [session, newchatBtn, chatHistoryList, knowledge, ChatBot,  upvote_btn, downvote_btn,clear_btn,regenerate_btn, stop_btn, InputText, SendBtn, generalChatButton , fileHistoryList, fileUpload, newFileBtn, fileChatBtn]). then(
            loadConversationFromSession, [chatHistoryList, session, ChatBot], [chatHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, clear_btn,regenerate_btn, SendBtn, InputText, knowledge, suggestionDefault, suggestion])

        fileUpload.change(fileUploadChange, [fileUpload, session], [fileUpload, session, fileHistoryList, ChatBot]).then(
            convertFileToJson,[fileUpload, session],[InputText]).then(
            initilizeConversationFile, [fileUpload, session, fileHistoryList], [ChatBot, fileUpload, upvote_btn, downvote_btn, stop_btn, regenerate_btn, clear_btn, InputText, SendBtn])
        
        fileHistoryList.change(loadConversationFileFromSession, [fileHistoryList, session, ChatBot], [fileHistoryList, ChatBot, upvote_btn, downvote_btn, stop_btn, regenerate_btn, clear_btn, SendBtn, InputText, suggestion, fileUpload])

        newFileBtn.click(uploadNewFile, [], [fileHistoryList, upvote_btn, downvote_btn, stop_btn, clear_btn,regenerate_btn, SendBtn, InputText, ChatBot, fileUpload, suggestion])

    return WebChat

if __name__ == "__main__":
    webchat = createUI()
    webchat.queue(concurrency_count=3)
    webchat.launch()