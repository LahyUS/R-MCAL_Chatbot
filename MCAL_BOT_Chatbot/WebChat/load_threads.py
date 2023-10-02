import gradio as gr
import re
import os
import sys
import shutil

sys.path.append("..")
from security import authSecurity
from controller import chatController, modelController
from helper.enumerate import RequestStatus as Status
from helper.enumerate import ErrorCode
from helper.enumerate import MessageReactCode
from helper.enumerate import ChatMode
from const_defined import * 

def addNewConversation():
    """
    Create new conversation (When press new chat button).
    """
    defaultOption = [["Create task list"], ["Ask for information about the document"]]
    instuction = "You can choose following below options to continue"
    return ([], gr.update(value=None),) + (gr.update(interactive=False),)*5 + (gr.update(interactive=True),)*2 + (gr.update(visible=False),) + (gr.update(visible=True,  value=defaultOption),)+ (gr.update(visible=True,  value=instuction),)

def initilizeConversationFile(file, session:gr.State, file_name:str):
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

def deleteConversation(title:str, session:gr.State):
    """Handle delete a conversation."""
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
   
def deleteConversationFile(file_name:str, session:gr.State):
    """Handle delete a conversation in file chat mode"""
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

def loadConversationFromSession(title:str, session:gr.State, conversation:list):
    """
    Load conversation of a specific <title>.
    """
    print("\n\n##########################################################")
    print("[Web-Server]____ loadConversationFromSession")

    # Check for content exist or not
    if isinstance(session, dict) and "content" in session:
        # Clone needed information of the latest conversation
        chatHistoryTitles = session["title"] 
        chatHistoryContents = session["content"] 
        reacts = session["content_react"] 
        
        if title in chatHistoryContents:
            notifyMarkdown = MSG_NOTIFY_REACHED_TO_CHAT_LIMIT
            # Get the previous chat of the current title
            history = chatHistoryContents[title] 

            # If change to another conversation, then disable default suggestion and suggestion of the previous conversation
            if(conversation != history): updateOptions = (gr.update(visible=False),) * 2
            else: updateOptions = (gr.update(),) * 2

            # Get knowkedge of conversation from latest chat with answer have string "You have chosen option **"
            knowledge = ""
            for chat in reversed(history): # For each Q&A turn
                if chat[1] is not None and "You have chosen option **" in chat[1]: # Filter conversation in specific knowledge field
                    scope = re.findall(r"\*\*(.*?)\*\*", chat[1]) # Remove unneccessary characters 
                    scopeKnowledge = scope[0].split(" -> ") # Split sentence to get the Knowledge field
                    if len(scopeKnowledge) > 1:
                        chosenOption = scopeKnowledge[1] # Get the Knowledge field
                        if len(scopeKnowledge) > 2:
                            for i in range(2, len(scopeKnowledge)):
                                chosenOption += " -> " + scopeKnowledge[i]
                        knowledge += ("Using knowledge in **" + chosenOption + "** to answer your question.")
                    break
            
            # Check if not exist knowledge -> disable showing knowledge to chat page
            if len(knowledge) == 0: updateKnowledge = gr.update(visible=False)
            else: updateKnowledge = gr.update(visible=True, value=knowledge)
            
            # Remove chat in conversation if this chat contain string "You have chosen option **", so that 
            # when checking number of chat in conversation we not count the chat when user choose option from suggestion
            if history is not None:
                tmpHistory = [item for item in history if item[1] is not None and 'You have chosen option **' not in item[1]]

            # Check number of chat in conversation if it reaches to limit
            if len(tmpHistory) < MAX_CHAT_IN_CONVERSATION:
                if isinstance(history[-1][1], str) and history[-1][1].find(notifyMarkdown) > 0:
                    # Remove notify that reached to limit of chat to conversation if exist
                    history[-1] = (history[-1][0], history[-1][1].replace(notifyMarkdown, ""))
                
                # Check if latest chat contain reactions
                if title in reacts:
                    # If latest chat contain reaction, disable upvote and downvote button
                    if len(reacts[title]) > 0 and isinstance(reacts[title][-1], int) and reacts[title][-1] > 0:
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 4 + (updateKnowledge,) + updateOptions
                    # If latest chat Not contain reaction, enable upvote and downvote button
                    else: 
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 4 + (updateKnowledge,) + updateOptions
            
            else:
                if isinstance(history[-1][1],str) and history[-1][1].find(notifyMarkdown) < 0:
                    # Append notify reached to limit of chat to conversation
                    history[-1] = (history[-1][0], history[-1][1] + notifyMarkdown)
                
                # Check if latest chat contain reactions
                if title in reacts:
                    if len(reacts[title]) > 0 and isinstance(reacts[title][-1], int) and reacts[title][-1] > 0:
                        # If latest chat contain reaction, disable upvote and downvote button
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
                    
                    else:
                        # If latest chat Not contain reaction, enable upvote and downvote button
                        return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
                
                return (gr.update(value=title, choices=chatHistoryTitles), gr.update(value=history),) + (gr.update(interactive=False),) * 3 + (gr.update(interactive=True),) * 2 + (gr.update(interactive=False),) * 2 + (updateKnowledge,) + updateOptions
    
    return (gr.update(value=None), gr.update(value=None),) +  (gr.update(),) * 7 + (gr.update(visible=False),) + (gr.update(),)*2

def loadLatestConversation(latestTitleCookie:str, session:gr.State):
    """
    From the latest title taken from cookie, load conversation in its scope.
    """
    print("\n\n##########################################################")
    print("[Web-Server]____ loadLatestConversation", latestTitleCookie)
    if len(latestTitleCookie) > 0:
        # Decode title cookie into title
        latestTitle = authSecurity.get_latest_title(latestTitleCookie) 

        # Check for valid latest title AND the availability of the current session
        if len(latestTitle) > 0 and "title" in session and latestTitle in session["title"] and "content" in session:
            history = session["content"][latestTitle] 
            knowledge = ""

            # Get knowledge from conversation
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
            
            if len(knowledge) == 0: updateKnowledge = gr.update(visible=False)
            else: updateKnowledge = gr.update(visible=True, value=knowledge)

            return (gr.update(choices=session["title"], value=latestTitle), "", session["content"][latestTitle],) + (gr.update(interactive=True),) * 4 + (gr.update(interactive=False),) + (gr.update(visible=False),) + (updateKnowledge,) 

    print("[Web-Server]++++ Invalid lastest title")
    return (gr.update(), "", gr.update()) + (gr.update(interactive=False),) * 5+ (gr.update(visible=True,  value=defaultOption),)+ (gr.update(visible=False),)

def loadHistoryChat(session:gr.State):
    """
    Load all history chat of the current user.
    """
    print("\n\n##########################################################")
    print("[Web-Server]____ loadHistoryChat")
    if isinstance(session, dict) and "token" in session and "user_id" in session:
        # Request history chat
        status, chatHistoryTitles, chatHistoryTitlesId, chatHistoryTitlesknowledge, chatHistoryContents, chatHistoryContentsId, chatHistoryContentsReact = chatController.loadChatHistory(session["user_id"], session["token"])
        if status == Status.SUCCESS:
            print(f"[Web-Server] loadHistoryChat is SUCCESS")
            if len(chatHistoryContentsReact) > 0 and len(chatHistoryContents) > 0 and len(chatHistoryTitles) > 0:
                # Update reaction of each chat
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
            
            # Save history chat to the session
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

def loadHistoryChatFile(session:gr.State):
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

def loadFileList(session:gr.State):
    print("[Web-Server]-----load File list")
    if "file_name" in session:
        chatHistoryFiles = session["file_name"]
        return gr.update(value=None, choices=chatHistoryFiles)
    return gr.update()

def loadConversationFileFromSession(file_name, session:gr.State, conversation):
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

def fileUploadChange(file, session:gr.State):
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

def uploadNewFile():
    print("---- uploadNewFile")
    return (gr.update(value=None),) + (gr.update(interactive=False),)*7 + (gr.update(visible=False),) + (gr.update(visible=True, value=None),) + (gr.update(visible=False),) 
