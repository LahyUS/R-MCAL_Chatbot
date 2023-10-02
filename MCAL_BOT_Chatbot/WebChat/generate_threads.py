import gradio as gr
import sys

sys.path.append("..")
from controller import chatController, modelController
from helper.enumerate import RequestStatus as Status

from helper.enumerate import StateCode
from helper.enumerate import ChatMode

from const_defined import *
from load_threads import * 

def extractRelatedQuestion(data:str):
    """
    Extract related questions from data that returned by model server.
    """
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
        
def extractReferenceLink(data:str):
    """
    Extract reference links from data that returned by model server.
    """
    #print("\n\n##########################################################")
    #print("[Web-Server]______ extractLinkReference")

    result = "\n<br>**Reference documents:**\n"
    # Find the index of the starting point of the reference documents section
    current_i = data.find("**Reference documents:**")
    # Find the index of the ending point of the reference documents section
    end_i = data.find("<br>.")
    
    #  Check if the reference documents section is found in the data.
    if current_i != -1:
        # Move the index to the first character after the "Reference documents:" string
        current_i += len(str("**Reference documents:**")) + 1
        # Iterate through the data within the reference documents section
        while current_i < end_i:
            rawReference = ""
            # Collect characters from the data until a newline character is encountered or the end of the reference documents section
            while current_i < end_i and data[current_i] != '\n':
                rawReference += data[current_i]
                current_i += 1
                
            if len(rawReference) > 0:
                # Remove any leading non-alphabetic characters from rawReference
                rawReference = re.sub(r'^[^a-zA-Z]+', '', rawReference)
                # If the last character of rawReference is a newline character, remove it
                if len(rawReference) > 0 and rawReference[-1] == '\n':
                    rawReference = rawReference[:-1]
                
                # Find the index of the "|" character, then get the page number
                page_index = rawReference.find("|")
                if page_index != -1:
                    page_index == int(page_index)
                    page = rawReference[page_index:]
                    rawReference = rawReference[:page_index]
                else:
                    page = ""

                # If the link is "external", list the PDF files in the folder indicated by rawReference. 
                # If there are PDF files present, choose the first file to display.
                if "external" in rawReference:
                    # List file in folder  
                    pdf_files = [file for file in os.listdir(PATH_TO_DATABASE + rawReference) if file.lower().endswith('.pdf')]
                    if len(pdf_files) > 0:
                        displayString = pdf_files
                        # Get the first file in folder (This folder has only one file)
                        rawReference += "/" + pdf_files[0]
                else:
                    # If the link is "internal", add the "internal/" prefix to rawReference.
                    rawReference = "internal/" + rawReference

                # Link displaying to user do not contain "internal" or "external" so we will remove it
                displayString = rawReference
                if "internal/" in displayString:
                    displayString = displayString.replace("internal/", "")
                if "external/" in displayString:
                    displayString = displayString.replace("external/", "")
                
                # Create an HTML-formatted link and adds it to the result string.
                '''
                + '<a href="': This part starts an HTML anchor (<a>) tag for creating a link.
                + "files/": This part is a relative path indicating the "files" directory on the document server.
                + '" target="_blank">': This continues the HTML anchor (<a>) tag, setting the link's target attribute to "_blank" to open the link in a new browser tab.
                + '</a> .Page ': This part closes the HTML anchor (<a>) tag and adds a space, followed by ".Page ".
                '''
                result += "- " + '<a href="' + DOCUMENT_SERVER_ADDRESS + "files/" + rawReference.replace("/", "!") + '" target="_blank">' + displayString + '</a>  .Page ' + page + '\n'
            if current_i < end_i and data[current_i] == '\n':
                current_i+= 1

    return result

def extractHTMLLink(data, prefix:str):
    """
    Extract HTML links from data that returned by model server.
    """
    #print("\n\n##########################################################")
    #print("[Web-Server]______ extractHTMLLink")

    result = "\n<br>**" + prefix +":**\n"
    header = "**" + prefix + ":**"
    # Find the index of the starting point of the section
    current_i = data.find(header)
    # Find the index of the ending point of thes section
    end_i = data.find("<br>.")
    
    #  Check if this section is found in the data.
    if current_i != -1:
        # Move the index to the first character after the header string
        current_i += len(header) + 1
        # Iterate through the data within content of the header
        while current_i < end_i:
            link = ""
            # Collect characters from the data until a newline character is encountered or the end of this section
            while current_i < end_i and data[current_i] != '\n':
                link += data[current_i]
                current_i += 1

            # If the last character is a newline character, remove it
            if len(link) > 0:
                if link[-1] == '\n':
                    link = link[:-1]
                # Create an HTML-formatted link and adds it to the result string.
                '''
                + '<a href="': This part starts an HTML anchor (<a>) tag for creating a link.
                + '</a>': This part closes the HTML anchor (<a>) tag and adds a space.
                '''
                result += "- " + '<a href="' + link + '">' + link + '</a>' + '\n'
            if current_i < end_i and data[current_i] == '\n':
                current_i += 1

    return result

def extract_link(latest_ans, current_ans, link_buf):
    # Check for the link style in the streamed data from the generator
    link_type = ""
    if "**Work Product links:**"     in current_ans: link_type = "Work Product links"
    elif "**Guideline links:**"      in current_ans: link_type = "Guideline links"
    elif "**Guideline:**"            in current_ans: link_type = "Guideline"
    elif "**Reference documents:**"  in current_ans: link_type = "Reference documents"
    elif "**Related question:**"     in current_ans: link_type = "Related question"

    link_start_index = current_ans.find(f"**{link_type}:**")
    related_question = ""
    updated_ans = current_ans
    guideline_link_temp_buf = ""

    if link_start_index != -1:
        if link_type == "Reference documents":
            link = extractReferenceLink(current_ans[link_start_index:])
            # Append result of extraction to answer
            updated_ans = latest_ans + link 

        elif link_type == "Work Product links":
            link = extractHTMLLink(current_ans[link_start_index:], prefix=link_type)
            # Append result of extraction to answer
            updated_ans = latest_ans + link 
            
        elif link_type == "Guideline links":
            link = extractHTMLLink(current_ans[link_start_index:], prefix=link_type)
            # Append result of extraction to answer
            updated_ans = latest_ans
            link = link.replace('<br>**Guideline links:**\n', "")
            guideline_link_temp_buf = link 

        elif link_type == "Guideline":
            # No need to update the latest_answer
            # No need to extract anything, just cat till the end of the string
            current_ans = current_ans[1:current_ans.find("<br>.")]
            updated_ans = latest_ans + "\n<br>" + current_ans + "\n" + "***Please refer to these guideline links for more detailed***" + link_buf

        elif link_type == "Related question":
            # No need to update the latest_answer
            updated_ans = latest_ans
            related_question = current_ans        

    return updated_ans, related_question, guideline_link_temp_buf
         
def generateAnswer(title:str, conversation:list, session:gr.State):
    """
    Send question to model server and get streammed data from it.
    """
    print("\n\n##########################################################")
    print("[Web-Server]______ generateAnswer")
    
    # Check for valid Chat mode
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT: 
        # Check for valid conversation with valid question
        if len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str) and len(conversation[-1][0]) > 0 and (conversation[-1][1] == None or len(conversation[-1][1]) <= 0): 
            question = conversation[-1][0] # Get question from the latest chat
        
            # Clone conversation content from session if available
            if "content" in session: chatHistoryContents = session["content"]
            else: chatHistoryContents = {}

            # Get streammed data from Model Server
            answer = ""
            link_buf = ""
            for streamStatus, ans, key in modelController.streamResponse(ChatMode.GENERAL_CHAT.value, session["token"], question, conversation):
                if streamStatus == Status.SUCCESS:
                    session["streaming_key"] = key
                    answer, currentRelatedQuestion, link_buf = extract_link(latest_ans=answer, current_ans=ans, link_buf=link_buf)

                    # Check for generated Related Questions. If contain suggestion question, extract them.
                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        #conversation[-1][1] = ans[:relatedQuestionPos]
                        #answer = ans[:relatedQuestionPos]
                        #chatHistoryContents[title] = conversation
                        relatedQuestion = extractRelatedQuestion(currentRelatedQuestion)
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    
                    # Update streammed data to the current answer
                    else:
                        conversation[-1][1] = answer
                        #answer = ans
                        chatHistoryContents[title] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                
                # If the streaming fail, prompt the fail message
                elif streamStatus == Status.FAIL or streamStatus == Status.ERROR:
                    print(f"[Web-Server]++++ status: ", streamStatus)
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM #[[]]
                    answer = " "
                    chatHistoryContents[title] = conversation
                    #chatHistoryContents[title][-1][1] = answer
                    session["streaming_key"] = None
                    # Update session
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return

            # After get the completed answer, send the conversation to database for storaging
            # Check for valid conversation, No need to save an empty or corrupted conversation
            addStatus = Status.FAIL
            if question != None and answer != None: 
                addStatus, msgID = chatController.addMessage(session["user_id"], session["token"], title, question, answer)

            # If update message to database OK, then update the session    
            if addStatus == Status.SUCCESS:
                session["content_id"][title].append(msgID)
                session["content"] = chatHistoryContents
                session["content_react"][title].append(None)
                session["streaming_key"] = None

                tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]
                if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
                    if isinstance(conversation[-1][1], str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return

                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            
            else: print("[Web-Server]++++ Update message FAIL")

        # If the question is not satisfied, Remove the latest empty chat        
        else: conversation = conversation[:-1]

        # Update session and return
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        return

    # Update session and return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def generateAnswerFile(file_name:str, conversation:list, session:gr.State):
    """
    Generate answer in file chat mode (This function has different returned values from the above function).
    """
    print("\n\n##########################################################")
    print("[Web-Server]______ generateAnswerFILE")

    # Check for valid Chat mode
    if "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        # Check for valid conversation with valid question
        if conversation is not None and len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str)  and len(conversation[-1][0]) > 0 and (conversation[-1][1] == None or len(conversation[-1][1]) <= 0):
            question = conversation[-1][0]
            
            if "content_file" in session: chatHistoryContents = session["content_file"]
            else: chatHistoryContents = {}

            # Clone conversation content from session if available
            index = session["file_name"].index(file_name)
            fileID = session["file_id"][index]
            path = "external/" + str(fileID)

            # Get streammed data from Model Server
            answer = ""
            for status, ans, key in modelController.streamResponse(ChatMode.FILE_CHAT.value, session["token"], question, conversation, path):
                if status == Status.SUCCESS:
                    session["streaming_key"] = key

                    # Check for generated Reference Documents
                    referLinkStartIndex = ans.find("**Reference documents:**")
                    endReferLinkSignal = "<br>."
                    endReferLink = ans.find(endReferLinkSignal)
                    if referLinkStartIndex != -1 and endReferLink != -1:
                        referLink = extractReferenceLink(ans[referLinkStartIndex:])
                        ans = ans[:referLinkStartIndex] + referLink + ans[endReferLink + len(endReferLinkSignal):]

                    # Check for generated Related Questions
                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1][1] = ans[:relatedQuestionPos]
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[file_name] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    
                    # Update streammed data to the current answer
                    else:
                        conversation[-1][1] = ans
                        answer = ans
                        chatHistoryContents[file_name] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                
                # If the streaming fail, prompt the fail message
                elif status == Status.FAIL or status == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return

            # After get the completed answer, send the conversation to database for Storaging
            # Check for valid conversation, No need to save an empty conversation
            if question != None or answer != None: 
                status, msgID = chatController.addMessageFile(session["user_id"], session["token"], file_name, question, answer)
            
            # If update message to database OK, then update the session    
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

            else: print("[Web-Server]++++ Update message FAIL")

        # If the question is not satisfied, Remove the latest empty chat      
        else: conversation = conversation[:-1]
        
        # Update session and return
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        print("[Web-Server].++++ End generate answer")
        return

    # Update session and return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def regenerateAnswer(title:str, conversation:list, session:gr.State):
    """Handle rgenerate answer. Simialar to generateAnswer but difference return value."""
    print("\n\n##########################################################")
    print("[Web-Server]____ regenerateAnswer")
    
    # Check for valid Chat mode
    if "chat_mode" in session and session["chat_mode"] == ChatMode.GENERAL_CHAT:
        # Check for valid conversation with valid question
        if len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str) and len(conversation[-1][0]) > 0:
            question = conversation[-1][0] # Get question from the latest chat
        
            # Clone conversation content from session if available
            if "content" in session: chatHistoryContents = session["content"]
            else: chatHistoryContents = {}
        
            # Get streammed data from Model Server
            answer = ""
            for streamStatus, ans, key in modelController.streamResponse(1, session["token"], question, conversation):
                if streamStatus == Status.SUCCESS:
                    session["streaming_key"] = key

                    # Check for generated Reference Documents
                    referLinkStartIndex = ans.find("**Reference documents:**")
                    endReferLinkSignal = "<br>."
                    endReferLink = ans.find(endReferLinkSignal)
                    if referLinkStartIndex != -1 and endReferLink != -1:
                        referLink = extractReferenceLink(ans[referLinkStartIndex:])
                        ans = ans[:referLinkStartIndex] + referLink + ans[endReferLink + len(endReferLinkSignal):]

                    # Check for generated Related Questions
                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1] = (conversation[-1][0], ans[:relatedQuestionPos])
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[title] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    
                    # Update streammed data to the current answer
                    else:
                        conversation[-1] = (conversation[-1][0], ans)
                        answer = ans
                        chatHistoryContents[title] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                
                # If the streaming fail, prompt the fail message
                elif streamStatus == Status.FAIL or streamStatus == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
            
            # After get the completed answer, send the conversation to database for updating 
            # Check for valid conversation, No need to save an empty conversation
            if question != None and answer != None: 
                updateStatus= chatController.updateMessage(session["token"], session["content_id"][title][-1], answer)
            
            # If update message to database OK, then update the session 
            if updateStatus == Status.SUCCESS:
                session["content"] = chatHistoryContents
                session["content_react"][title][-1] = 0
                session["streaming_key"] = None

                tmpHistory = [item for item in conversation if 'You have chosen option **' not in item[1]]

                if len(tmpHistory) >= MAX_CHAT_IN_CONVERSATION:
                    if isinstance(conversation[-1][1], str) and conversation[-1][1].find(MSG_NOTIFY_REACHED_TO_CHAT_LIMIT) < 0:
                        conversation[-1] = (conversation[-1][0], conversation[-1][1] + MSG_NOTIFY_REACHED_TO_CHAT_LIMIT)
                    
                    yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(interactive=False),) * 2 + (gr.update(interactive=True),)*2 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return
                
                yield (conversation, session,) + (gr.update(interactive=True),)* 2 + (gr.update(value=None, interactive=True),) + (gr.update(interactive=True),)* 3 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(),) + (gr.update(visible=False),)
                return
            
            else: print("[Web-Server]++++ Update message FAIL")
        
        # If the question is not satisfied, Remove the latest empty chat 
        else: conversation = conversation[:-1]
        
        # Update session and return
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        return

    # Update session and return
    yield (conversation, session,) + (gr.update(),) * 10
    return

def regenerateAnswerFile(file_name:str, conversation:list, session:gr.State):
    """Handle rgenerate answer. Simialar to generateAnswerFile but difference return value."""
    print("\n\n##########################################################")
    print("[Web-Server]____ regenerateAnswerFile")
    
    # Check for valid Chat mode
    if "chat_mode" in session and session["chat_mode"] == ChatMode.FILE_CHAT:
        # Check for valid conversation with valid question
        if conversation is not None and len(conversation) > 0 and len(conversation[-1]) > 0 and isinstance(conversation[-1][0], str) and len(conversation[-1][0]) > 0 and (conversation[-1][1] == None or len(conversation[-1][1]) <= 0):
            question = conversation[-1][0]
            
            if "content_file" in session: chatHistoryContents = session["content_file"]
            else: chatHistoryContents = {}
        
            # Clone conversation content from session if available
            index = session["file_name"].index(file_name)
            fileID = session["file_id"][index]
            path = "external/" + str(fileID)

            # Get streammed data from Model Server
            answer = ""
            for status, ans, key in modelController.streamResponse(2, session["token"], question, conversation, path):
                if status == Status.SUCCESS:
                    session["streaming_key"] = key

                    # Check for generated Reference Documents
                    referLinkStartIndex = ans.find("**Reference documents:**")
                    endReferLinkSignal = "<br>."
                    endReferLink = ans.find(endReferLinkSignal)
                    if referLinkStartIndex != -1 and endReferLink != -1:
                        referLink = extractReferenceLink(ans[referLinkStartIndex:])
                        ans = ans[:referLinkStartIndex] + referLink + ans[endReferLink + len(endReferLinkSignal):]

                    # Check for generated Related Questions
                    relatedQuestionPos = ans.find("**Related question:**")
                    if relatedQuestionPos != -1:
                        conversation[-1][1] = ans[:relatedQuestionPos]
                        answer = ans[:relatedQuestionPos]
                        chatHistoryContents[file_name] = conversation
                        relatedQuestion = extractRelatedQuestion(ans[relatedQuestionPos:])
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.REGENERATING,) + (gr.update(visible=True, value=relatedQuestion),) + (gr.update(visible=False),)
                    
                    # Update streammed data to the current answer
                    else:
                        conversation[-1][1] = ans
                        answer = ans
                        chatHistoryContents[file_name] = conversation
                        yield (conversation, session,) + (gr.update(interactive=False),)* 6 + (gr.update(interactive=True),) + (StateCode.GENERATING,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                
                # If the streaming fail, prompt the fail message
                elif status == Status.FAIL or status == Status.ERROR:
                    conversation[-1][1] = MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM
                    session["streaming_key"] = None
                    yield (conversation, session,) + (gr.update(interactive=False),)* 7 + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
                    return

            # After get the completed answer, send the conversation to database for Updating
            # Check for valid conversation, No need to save an empty conversation
            if question != None or answer != None: 
                status = chatController.updateMessageFile(session["token"], session["content_id_file"][file_name][-1], answer)
            
            # If update message to database OK, then update the session    
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

        # If the question is not satisfied, Remove the latest empty chat          
        else: conversation = conversation[:-1]

        # Update session and return
        session["streaming_key"] = None
        yield (conversation, session,) + (gr.update(interactive=True),)* 6 + (gr.update(interactive=False),) + (StateCode.NONE,) + (gr.update(visible=False),) + (gr.update(visible=False),)
        print("[Web-Server]++++ End generate answer")
        return

    # Update session and return    
    yield (conversation, session,) + (gr.update(),) * 10
    return
