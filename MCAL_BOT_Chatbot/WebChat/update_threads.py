import gradio as gr
import sys

sys.path.append("..")
from security import authSecurity
from controller import chatController
from helper.enumerate import RequestStatus as Status
from helper.enumerate import StateCode
from helper.enumerate import ChatMode
from helper.enumerate import ChatLimit

from const_defined import * 


def updateUserIDFromCookie(tokenCookieDefault:gr.HTML, session:gr.State):
    """
    Load information from access token which have been taken from cookie
    """
    if isinstance(tokenCookieDefault, str) and len(tokenCookieDefault) > 0:
        tokenSession = authSecurity.get_current_token(tokenCookieDefault)
        if len(tokenSession) > 0:
            user_id, token = authSecurity.decodeToken(tokenSession)
            session["token"] = token
            session["user_id"] = user_id
            session["chat_mode"] = ChatMode.GENERAL_CHAT
    return session

def updateLatestTitleToCookie(title:str, session:gr.State):
    """
    Create token of the latest title for saving to cookie.
    """

    print("\n\n##########################################################")
    print("[Web-Server]____ updateLatestTitleToCookie")
    if "title" in session:
        if title in session["title"]  or ((title == None or title == "") and len(session["title"]) > 0):  
            tokenData = {
                "title":title
            }
            ret = authSecurity.create_token(tokenData) # Create a new token for this current title
            print(f"[Web-Server] updateLatestTitleToCookie:- {ret}")
            return ret

    return ""

def updateChatHistoryList(title:str, conversation:list, session:gr.State):
    """
    After update UI when user submitting question, update the title of conversation if needed.
    """
    print("[Web-Server]______ updateChatHistoryList")

    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        # If chat title has existed, do nothing
        if title is not None and len(title) > 0 and len(conversation[-1][0]) > 0 : 
            return title, session

        # If new chat without title
        elif len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str) and len(conversation[-1][0]) > 0:
            # Assign title to the first query of the conversation
            title = conversation[-1][0] 
            
            # Cutdown title if too long
            if len(title) > ChatLimit.TITLE_LIMIT.value:
                title = title[:ChatLimit.TITLE_LIMIT.value]

            # Clone the previous title list
            if "title" in session:  chatHistoryTitles = session["title"]
            else: chatHistoryTitles = []
            
            # Check if title is duplicated in the HistoryTitles List, then update name for the current
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

            # Send new title to database server for storaging. If request is successfull, update the session
            status, titleID = chatController.newTitle(session["user_id"], session["token"], title)
            if status == Status.SUCCESS:
                # Append the new title if success
                chatHistoryTitles.append(title)
                session["title"] = chatHistoryTitles
                
                # Clone the previous title_id list from the session
                if "title_id" in session:
                    chatHistoryTitlesID = session["title_id"] 
                else:
                    chatHistoryTitlesID = []
                
                # Clone the previous content list from the session
                if "content" in session:
                    chatHistoryContents = session["content"]
                else:
                    chatHistoryContents = {}

                # Update the session
                chatHistoryTitlesID.append(titleID)
                session["title_id"] = chatHistoryTitlesID 
                chatHistoryContents[title] = conversation 
                session["content"] = chatHistoryContents
                session["content_id"][title] = []
                session["content_react"][title] = []
                
                # Update the dropdown chatHistoryTitles component and the current session
                return gr.update(choices=chatHistoryTitles, value=title), session

    # Update the dropdown chatHistoryTitles component and the current session
    return gr.update(), session

def updateConversationDefault(title:str, conversation:list, session:gr.State):
    print("[Web-Server]+++ updateConversationDefault")

    if len(conversation[-1][0]) > 0 and conversation[-1][0] != "Ok":
        if "content" in session:
            chatHistoryContents = session["content"]
        else:
            chatHistoryContents = {}

        status = Status.FAIL
        if title != None and title != '':
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
        
        # TODO
        else:
            print("[Web-Server] Update message ERROR")
            yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),) * 2
            return

    else:
        if conversation[-1][0] == "Ok":
            conversation.pop()
        print("[Web-Server] Update message FAIL")
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),) * 2
        return
