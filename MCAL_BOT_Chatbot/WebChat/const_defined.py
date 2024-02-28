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
                    console.log("[DEBUG] ##################");
                    console.log("[DEBUG] setAccessToken");
                    const d = new Date();
                    d.setTime(d.getTime() + (""" + str(COOKIE_EXPIRE_TIME_SECOND) + """ * 1000));
                    let expires = "expires="+d.toUTCString();
                    if(typeof token === 'string' && token.trim() !== '')
                    {
                        document.cookie = "authorization=" + token + ";" + expires + ";path=/"; 
                        console.log("[DEBUG] token:", token);
                        console.log("[DEBUG] document.cookie:", document.cookie);
                    }
                }"""

# Function set latest tiltle cookie   
setLastestTitleToken = """(token) => {
                    console.log("[DEBUG] ##################");
                    console.log("[DEBUG] setLastestTitleToken");
                    if(typeof token === 'string' && token.trim() !== '')
                    {
                        document.cookie = "lastTitle=" + token + ";path=/"; 
                        console.log("[DEBUG] document.cookie:", document.cookie);
                    }
                }"""
                
# Function get access token cookie               
getAccessToken = """() => {
                    console.log("[DEBUG] ##################");
                    console.log("[DEBUG] getAccessToken");
                    let name = "authorization" + "=";
                    let ca = document.cookie.split(';');
                    let result="";
                    for(let i = 0; i < ca.length; i++)
                    {
                        let c = ca[i];
                        while (c.charAt(0) == ' ') 
                        {
                            c = c.substring(1);
                        }
                        if (c.indexOf(name) == 0) 
                        {
                            console.log("[DEBUG] Found authorization cookie:", c.substring(name.length, c.length));
                            return c.substring(name.length, c.length) + "E";
                        }
                    }
                    return ""
                }"""

# Function get latest title cookie                 
getLatestTitleToken = """() => {
                    console.log("[DEBUG] ##################");
                    console.log("[DEBUG] getLatestTitleToken");
                    let name = "lastTitle" + "=";
                    let ca = document.cookie.split(';');
                    let result="";
                    for(let i = 0; i < ca.length; i++) 
                    {
                        let c = ca[i];
                        while (c.charAt(0) == ' ') 
                        {
                            c = c.substring(1);
                        }
                        if (c.indexOf(name) == 0) 
                        {
                            console.log("[DEBUG] Found lastTitle cookie:", c.substring(name.length, c.length));
                            return c.substring(name.length, c.length) + "E";
                        }
                    }
                    return ""
                }"""

# Function delete access token cookie                
deleteAccessToken = """() => {
                    console.log("[DEBUG] ##################");
                    console.log("[DEBUG] deleteAccessToken");
                    document.cookie = "authorization" + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    console.log("[DEBUG] Deleted authorization cookie");
                }"""
                
# Default suggestion list               
#defaultOption = [["Create task list"], ["Ask for information about the document"]]
defaultOption = [["To be developed feature No.01"], ["To be developed feature No.02"]]