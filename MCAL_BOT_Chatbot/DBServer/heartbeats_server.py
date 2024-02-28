import gradio as gr
from flask import Flask, request, jsonify, session
import time
from flask_session import Session
import threading
import uuid

app = Flask(__name__)

app = Flask(__name__)
app.secret_key = 'af84e3cdeaed21a9220fb4fb7a9611de9d1abf85e0642ef50c71076a9fcba177'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False

#app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Dictionary to track active sessions
active_sessions = {}
sessions_to_remove = set()
INTERVAL_HERATBEAT = 10
# Create a lock for session data access
session_lock = threading.Lock()

# Notify the Gradio Web server about the dead session
def notify_gradio_session_dead(session_id):
    # Implement a mechanism to notify the Gradio server
    # This depends on how you have set up communication with Gradio
    # You may use HTTP requests, websockets, or other communication methods
    print(f"[DEBUG] notify_gradio_session_dead")


# Background task to check for inactive sessions
def check_inactive_sessions():
    while True:
        current_time = time.time()
        # Create a copy of the active_sessions dictionary

        for token, (user_id, last_heartbeat) in active_sessions.items():
            print(f"[DEBUG] check_inactive_sessions is handling")
            if current_time - last_heartbeat > INTERVAL_HERATBEAT:  # Adjust this threshold as needed
                print(f"[DEBUG] Session {user_id} is considered dead.")
                sessions_to_remove.add((token, user_id))
                print(f"[DEBUG] sessions_to_remove after adding: {sessions_to_remove}")

        time.sleep(5)  # Check every 5 seconds

# Start the background task
background_task = threading.Thread(target=check_inactive_sessions)
background_task.daemon = True
background_task.start()


@app.route('/browser_close', methods=['POST'])
def browser_close():
    print(f"[DEBUG] browser_close")

def generate_session_id():
    # Generate a unique session ID using a combination of a timestamp and a random UUID
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4().hex)
    session_id = f"{timestamp}-{unique_id}"
    return session_id

@app.route('/interval_check', methods=['GET'])
def interval_check():
    print(f"\n[DEBUG] ### interval_check")
    try:
        # Clone session data to be removed
        ret_session = list(sessions_to_remove)

        print(f"[DEBUG] ret_session: {ret_session}")
        # Remove the sessions outside of the loop
        with session_lock:
            for token, user_id in ret_session:
                del active_sessions[token]
                sessions_to_remove.remove((token, user_id))

        print(f"[DEBUG] sessions_to_remove: {sessions_to_remove}")
        print(f"[DEBUG] active_sessions: {active_sessions}")
        return jsonify({
                    "status": 1,
                    "msg": ret_session
                }) 

    except Exception as e:
        print("[DEBUG] Error in interval_check:", e)
        return jsonify({"status": 0,
                        "msg": "Internal server error"}), 500

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json()
        print(f"\n[DEBUG] ### heartbeat")
        print(f"[DEBUG] cookies: {request.cookies}")
        print(f"[DEBUG] data: {data}")

        if "user_id" not in data or "token" not in data:
            return jsonify({
                        "status": 2,
                        "msg": "Invalid request data"
                    }), 400

        token = data['token']
        user_id = data['user_id']
        current_time = time.time()

        with session_lock:
            active_sessions[token] = (user_id, current_time)

        #tmp_usr_id, last_heartbeat = active_sessions.get(token)
        print(f"[DEBUG] Heartbeat received successfully")
        print(f"[DEBUG] current active_sessions: {active_sessions}")
        return jsonify({
                    "status": 1,
                    "msg": "Heartbeat received"
                }) 
    except:
        return jsonify({
                    "status": 0,
                    "msg": "Heartbeat received"
                }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1236)
