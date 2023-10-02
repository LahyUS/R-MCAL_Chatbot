DOCUMENT_SERVER_ADDRESS = "http://127.0.0.1:2234/"
PATH_TO_DATABASE = ""
COOKIE_EXPIRE_TIME_SECOND = 60
MAX_CHAT_IN_CONVERSATION = 15
MAX_CHAT_IN_CONVERSATION_FILE = 15

MSG_NOTIFY_UPVOTE = """<br><br>  <span style="color: green;">**👍 Upvoted**</span>"""
MSG_NOTIFY_DOWNVOTE = """<br><br>  <span style="color: red;">**👎 Downvoted**</span>"""
MSG_NOTIFY_REACHED_TO_CHAT_LIMIT = """<br><span></span><br>  <span style="color: orange;">**You have reached the chat limit in this conversation - """ + str(MAX_CHAT_IN_CONVERSATION) + """ messages**</span>"""
MSG_NOTIFY_MODEL_SERVER_HAS_PROBLEM = """<span style="color:red">**Error:** Model server has problem.</span>"""

###### JavaScript functions for handle cookie 
# Function set access token cookie
setAccessToken = """(token) => {
                    const d = new Date();
                    d.setTime(d.getTime() + (""" + str(COOKIE_EXPIRE_TIME_SECOND) + """ * 1000));
                    let expires = "expires="+d.toUTCString();
                    if(typeof token === 'string' && token.trim() !== ''){
                        document.cookie = "authorization="+token+ ";" + expires + ";path=/"; 
                    }
                }"""

#Function set latest tiltle cookie   
setLastestTitleToken = """(token) => {
                    if(typeof token === 'string' && token.trim() !== ''){
                        console.log("set title kkkkkkkk");
                        document.cookie = "lastTitle="+token+ ";path=/"; 
                    }
                }"""
                
#Function get access token cookie               
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

#Function get latest title cookie                 
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

#Function delete access token cookie                
deleteAccessToken = """() => {
                    document.cookie = "authorization" + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                }"""
                
# Default suggestion list               
defaultOption = [["Create task list"], ["Ask for information about the document"]]