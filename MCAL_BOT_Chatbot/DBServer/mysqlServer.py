import mysql.connector
from flask import Flask, request, jsonify
import json
from functools import wraps

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="rvc",
    passwd="Pass1234",
    database="chatbot_db"
)

app = Flask(__name__)

app.config["api-key"] = "af84e3cdeaed21a9220fb4fb7a9611de9d1abf85e0642ef50c71076a9fcba150"

def api_key_check(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        print("api key check")
        if "api-key" not in request.headers:
            return jsonify({'Alert!': 'API key is missing!'}), 401
        else:
            api_key = request.headers["api-key"]
            if api_key != app.config["api-key"]:
                return jsonify({'Message': 'Invalid API key'}), 403
        return func(*args, **kwargs)
    return decorated

def token_check(token):
    mycursor = mydb.cursor()
    sql = "SELECT * FROM users WHERE token = %s"
    val = [token]
    mycursor.execute(sql, list(val))
    result = mycursor.fetchone()
    if result:
        return True
    return False
 
@app.route('/login', methods=["POST"])
@api_key_check
def login():
    data = request.get_json()
    if "username" in data and "password" in data:
        username = data['username']
        password = data['password']
        mycursor = mydb.cursor()
        
        # Check if the user is already logged in
        sql_check_login_status = "SELECT login_status FROM users WHERE username = %s"
        mycursor.execute(sql_check_login_status, (username,))
        login_status = mycursor.fetchone()
        print(f"[DEBUG] login_status: {login_status}")
        print(f"[DEBUG] login_status[0]: {login_status[0]}")
        if login_status and (login_status[0] == 1 or  login_status[0] == True):
            print(f"[DEBUG] Duplicate user login")
            return jsonify({
                "status": 3,
                "msg": "User is already logged in"
            })

        # If not logged in, proceed to verify the username and password
        sql_verify_login = "SELECT * FROM users WHERE username = %s AND password = %s"
        val = (username, password)
        mycursor.execute(sql_verify_login, val)
        result = mycursor.fetchone()

        if result:
            # Set the login_status to True
            sql_set_login_status = "UPDATE users SET login_status = TRUE WHERE username = %s"
            mycursor.execute(sql_set_login_status, (username,))
            mydb.commit()

            return jsonify({
                "status": 1,
                "isAdmin": result[3],
                "user_id": result[0],
                "msg": "Login successfully",
                "token": result[4]
            })
        else:
            return jsonify({
                "status": 2,
                "msg": "Username or password incorrect"
            })
            
    return jsonify({'Message': 'Invalid data'}), 403


@app.route('/logout', methods=["POST"])
@api_key_check
def logout():
    data = request.get_json()
    if "user_id" in data:
        user_id = data['user_id']
        mycursor = mydb.cursor()

        # Check if the user is already logged in
        sql_check_login_status = "SELECT login_status FROM users WHERE id = %s"
        mycursor.execute(sql_check_login_status, (user_id,))
        login_status = mycursor.fetchone()

        if login_status and login_status[0]:
            # Set the login_status to False
            sql_set_login_status = "UPDATE users SET login_status = FALSE WHERE id = %s"
            mycursor.execute(sql_set_login_status, (user_id,))
            mydb.commit()

            return jsonify({
                "status": 1,
                "msg": "Logout successful"
            })
        else:
            return jsonify({
                "status": 2,
                "msg": "User is not currently logged in"
            })
    return jsonify({'Message': 'Invalid data'}), 403


# General chat mode APIs

@app.route('/loadChatHistories', methods=["POST"])
@api_key_check
def loadChatHistories(*args, **kwargs):
    data = request.get_json()
    if "token" in data and "user_id" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = """
                SELECT ct.id, ct.name, ct.knowledge, m.id, m.question, m.answer, m.react
                FROM chat_titles ct
                LEFT JOIN messages m ON ct.id = m.title_id
                WHERE ct.user_id = %s AND ct.name IS NOT NULL
                ORDER BY m.id
            """
            val = [userID]
            mycursor.execute(sql, list(val))
            messagesList = mycursor.fetchall()
            response = {}
            
            if len(messagesList) == 0:
                response["status"] = 0
            else:
                response["status"] = 1
                dataArray = []
                for row in messagesList:
                    if(row[0] not in (d["title_id"] for d in dataArray)):
                        data = {
                                "title_id" : row[0],
                                "title" : row[1],
                                "title_knowledge" : row[2],
                                "message_id" : [],
                                "message_react" : [],
                                "message": []
                        }
                        dataArray.append(data)
                    
                    for d in dataArray:
                        if d["title_id"] == row[0]:
                            d["message_id"].append(row[3])
                            d["message_react"].append(row[6])
                            d["message"].append((row[4], row[5]))
                            break
                    
                response["data"] = dataArray
            
            return json.dumps(response)
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

@app.route('/newTitle', methods=["POST"])
@api_key_check
def newTitle(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "title" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = "SELECT * FROM chat_titles WHERE name = %s AND user_id = %s"
            val = [data["title"], userID]
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            print(result)
            if(result is None):
                mycursor = mydb.cursor()
                sql = "INSERT INTO chat_titles (user_id, name) VALUES (%s, %s)"
                val = (userID, data["title"])
                mycursor.execute(sql, val)
                titleID = mycursor.lastrowid
                mydb.commit()
                
                return jsonify({
                    "status":1,
                    "title_id": titleID
                })
            return jsonify({
                "status":0
            })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403
    
@app.route('/newMessage', methods=["POST"])
@api_key_check
def newMessage(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "title" in data and "question" in data and "answer" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = "SELECT * FROM chat_titles WHERE name = %s AND user_id = %s"
            val = [data["title"], userID]
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            print(result)
            if(result is None):
                mycursor = mydb.cursor()
                sql = "INSERT INTO chat_titles (user_id, name) VALUES (%s, %s)"
                val = (userID, data["title"])
                mycursor.execute(sql, val)
                mydb.commit()
                
            elif result:
                mycursor = mydb.cursor()
                sql = "INSERT INTO messages (title_id, question, answer) VALUES (%s, %s, %s)"
                val = (result[0], data["question"], data["answer"])
                mycursor.execute(sql, val)
                
                msgID = mycursor.lastrowid
                
                mydb.commit()
                
                return jsonify({
                    "status":1,
                    "message_id": msgID
                })
            else:
                return jsonify({
                    "status":0
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

@app.route('/updateMessage', methods=["POST"])
@api_key_check
def updateMessage(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "message_id" in data and "answer" in data:
        if token_check(data["token"]):
            message_id = data["message_id"]
            answer = data["answer"]
            mycursor = mydb.cursor()
            sql = "UPDATE messages SET answer = %s, react = %s WHERE id = %s"
            val = (answer, 0, message_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
            
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                print("mysql.connector.Error occured")
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403
        
@app.route('/checkToken', methods=["POST"])
@api_key_check
def checkToken(*args, **kwargs):    
    data = request.get_json()
    if token_check(data["token"]):
        return jsonify({
            "status":1
        })
        
    return jsonify({
        "status":0
    })
    
@app.route('/submitReact', methods=["POST"])
@api_key_check
def submitReact(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "message_id" in data and "react" in data:
        if token_check(data["token"]):
            message_id = data["message_id"]
            react = data["react"]
            mycursor = mydb.cursor()
            sql = "UPDATE messages SET react = %s WHERE id = %s"
            val = (react, message_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
                print(f"[DEBUG] submitReact OK")
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                print(f"[DEBUG] submitReact Connection Error")
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        print(f"[DEBUG] submitReact Invalid Token")
        return jsonify({"status":0, 'msg': 'Invalid token'}), 403

    print(f"[DEBUG] submitReact Invalid Data")
    return jsonify({"status":0, 'msg': 'Invalid data'}), 403

@app.route('/submitFeedback', methods=["POST"])
@api_key_check
def submitFeedback(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "message_id" in data and "feedback" in data:
        if token_check(data["token"]):
            message_id = data["message_id"]
            print(f"[DEBUG] message_id type: {type(message_id)} - Value: {message_id}")
            feedback = data["feedback"]
            print(f"[DEBUG] feedback type: {type(feedback)} - Value: {feedback}")
            mycursor = mydb.cursor()
            sql = "UPDATE messages SET feedback = %s WHERE id = %s"
            val = (feedback, message_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
            
                print(f"[DEBUG] submitFeedback OK")
                return jsonify({
                    "status":1
                })

            except mysql.connector.Error as error:
                print(f"[DEBUG] submitFeedback Connection Error")
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        
        print(f"[DEBUG] submitFeedback Invalid Token")
        return jsonify({"status":0, 'msg': 'Invalid token'}), 403
    
    print(f"[DEBUG] submitFeedback Invalid Data")
    return jsonify({"status":0, 'msg': 'Invalid data'}), 403

@app.route('/deleteConversation', methods=["POST"])
@api_key_check
def deleteConversation(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "title_id" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            titleID = data["title_id"]
            mycursor = mydb.cursor()
            sql = "DELETE FROM chat_titles WHERE id = %s AND user_id = %s"
            val = [titleID, userID]
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
                
                mycursor = mydb.cursor()
                sql = "DELETE FROM messages WHERE title_id = %s"
                val = [titleID]
                
                mycursor.execute(sql, list(val))
                mydb.commit()
                
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                return jsonify({
                    "status":0,
                    "msg":error
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

@app.route('/updateKnowledge', methods=["POST"])
@api_key_check
def updateKnowledge(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "title_id" in data and "knowledge" in data:
        if token_check(data["token"]):
            title_id = data["title_id"]
            knowledge = data["knowledge"]
            mycursor = mydb.cursor()
            sql = "UPDATE chat_titles SET knowledge = %s WHERE id = %s"
            val = (knowledge, title_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
            
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        return jsonify({"status":0, 'msg': 'Invalid token'}), 403
    return jsonify({"status":0, 'msg': 'Invalid data'}), 403

# File chat mode APIs

@app.route('/loadChatHistoriesFile', methods=["POST"])
@api_key_check
def loadChatHistoriesFile(*args, **kwargs):
    data = request.get_json()
    if "token" in data and "user_id" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = """
                SELECT cf.id, cf.file_name, mf.id, mf.question, mf.answer, mf.react
                FROM chat_files cf
                LEFT JOIN messages_file mf ON cf.id = mf.file_id
                WHERE cf.user_id = %s
                ORDER BY mf.id
            """
            val = [userID]
            mycursor.execute(sql, list(val))
            messagesList = mycursor.fetchall()
            response = {}

            print("-=-=-=----", messagesList)
            
            if len(messagesList) == 0:
                response["status"] = 0
            else:
                response["status"] = 1
                dataArray = []
                for row in messagesList:
                    if(row[0] not in (d["file_id"] for d in dataArray)):
                        data = {
                                "file_id" : row[0],
                                "file_name" : row[1],
                                "message_id" : [],
                                "message_react" : [],
                                "message": []
                        }
                        dataArray.append(data)
                    
                    for d in dataArray:
                        if d["file_id"] == row[0]:
                            d["message_id"].append(row[2])
                            d["message_react"].append(row[5])
                            d["message"].append((row[3], row[4]))
                            break
                    
                response["data"] = dataArray
            
            return json.dumps(response)
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

@app.route('/newFile', methods=["POST"])
@api_key_check
def newFile(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "file_name" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = "SELECT * FROM chat_files WHERE file_name = %s AND user_id = %s"
            val = [data["file_name"], userID]
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            print(result)
            if(result is None):
                mycursor = mydb.cursor()
                sql = "INSERT INTO chat_files (user_id, file_name) VALUES (%s, %s)"
                val = (userID, data["file_name"])
                mycursor.execute(sql, val)
                fileID = mycursor.lastrowid
                mydb.commit()
                
                return jsonify({
                    "status":1,
                    "file_id": fileID
                })
            return jsonify({
                "status":0
            })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403
    
@app.route('/newMessageFile', methods=["POST"])
@api_key_check
def newMessageFile(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "file_name" in data and "question" in data and "answer" in data:
        print("newMessageFile IF 1 OKKKK")
        if token_check(data["token"]):
            print("newMessageFile IF 2 OKKKK")
            userID = data["user_id"]
            mycursor = mydb.cursor()
            sql = "SELECT * FROM chat_files WHERE file_name = %s AND user_id = %s"
            val = [data["file_name"], userID]
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            print(result)
            if result:
                print("newMessageFile IF 3 OKKKK")
                mycursor = mydb.cursor()
                sql = "INSERT INTO messages_file (file_id, question, answer) VALUES (%s, %s, %s)"
                val = (result[0], data["question"], data["answer"])
                mycursor.execute(sql, val)
                
                msgID = mycursor.lastrowid
                
                mydb.commit()
                
                return jsonify({
                    "status":1,
                    "message_id": msgID
                })
            else:
                return jsonify({
                    "status":0
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

@app.route('/updateMessageFile', methods=["POST"])
@api_key_check
def updateMessageFile(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "message_id" in data and "answer" in data:
        if token_check(data["token"]):
            message_id = data["message_id"]
            answer = data["answer"]
            mycursor = mydb.cursor()
            sql = "UPDATE messages_file SET answer = %s, react = %s WHERE id = %s"
            val = (answer, 0, message_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
            
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                print("mysql.connector.Error occured")
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403
    
@app.route('/submitReactFile', methods=["POST"])
@api_key_check
def submitReactFile(*args, **kwargs):    
    data = request.get_json()
    if "token" in data and "user_id" in data and "message_id" in data and "react" in data:
        if token_check(data["token"]):
            message_id = data["message_id"]
            react = data["react"]
            mycursor = mydb.cursor()
            sql = "UPDATE messages_file SET react = %s WHERE id = %s"
            val = (react, message_id)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
            
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                return jsonify({
                    "status":0,
                    "msg" : error
                })
        return jsonify({"status":0, 'msg': 'Invalid token'}), 403
    return jsonify({"status":0, 'msg': 'Invalid data'}), 403

@app.route('/deleteConversationFile', methods=["POST"])
@api_key_check
def deleteConversationFile(*args, **kwargs):    
    print("---- deleteConversationFile")
    data = request.get_json()
    if "token" in data and "user_id" in data and "file_id" in data:
        if token_check(data["token"]):
            userID = data["user_id"]
            fileID = data["file_id"]
            mycursor = mydb.cursor()
            sql = "DELETE FROM chat_files WHERE id = %s AND user_id = %s"
            val = [fileID, userID]

            print("===", fileID)
            
            try:
                mycursor.execute(sql, val)
                mydb.commit()
                
                mycursor = mydb.cursor()
                sql = "DELETE FROM messages_file WHERE file_id = %s"
                val = [fileID]
                
                mycursor.execute(sql, list(val))
                mydb.commit()
                
                return jsonify({
                    "status":1
                })
            except mysql.connector.Error as error:
                return jsonify({
                    "status":0,
                    "msg":error
                })
        return jsonify({'Message': 'Invalid token'}), 403
    return jsonify({'Message': 'Invalid data'}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234)
