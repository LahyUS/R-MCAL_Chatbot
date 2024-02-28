from flask import Flask, send_file
import json
import os
import mimetypes

PATH_TO_DATABASE = "/home/banvien/Khanh/Renesas/DataBase/"

try:
    with open("../config.json", 'r') as file:
        config = json.load(file)
        if len(config) > 0:
            PATH_TO_DATABASE = config["path_to_database"]
            print(PATH_TO_DATABASE)
except FileNotFoundError:
    print("Configuration file not found")

MSG_NOTIFY_FILE_NOT_FOUND = """<!DOCTYPE html>
                                <html>
                                <head>
                                    <title>File Not Found</title>
                                    <style>
                                        .notification {
                                            background-color: #f8d7da;
                                            color: #721c24;
                                            padding: 10px;
                                            margin-bottom: 10px;
                                            border: 1px solid #f5c6cb;
                                            border-radius: 4px;
                                        }
                                    </style>
                                </head>
                                <body>
                                    <div class="notification">
                                        <h3>File Not Found</h3>
                                        <p>The requested file could not be found.</p>
                                    </div>
                                </body>
                                </html>"""

app = Flask(__name__)

def buildFolderTree(root_path, result):
    result[root_path] = []
    for f in os.scandir(root_path):
        if f.is_dir():
            obj = {}
            obj[f.name] = buildFolderTree(root_path+f.name+"/", result)
            result[root_path].append(obj)
    return result[root_path]
 
@app.route('/files/<filepath>', methods=["GET", "POST"])
def get_file(filepath):

    filepath = filepath.replace("!", "/")
    print(f"[DEBUG] filepath: {filepath}")
    file_path = os.path.join(PATH_TO_DATABASE, filepath)
    print(f"[DEBUG] file_path: {file_path}")

    if os.path.exists(file_path):
        print(f"[DEBUG] Filepath exists")

        filename = os.path.basename(file_path)
        _, file_extension = os.path.splitext(filename)
        print(f"[DEBUG] filename: {filename}")
        

        file_extension = file_extension[1:]
        print(f"[DEBUG] file_extension: {file_extension}")
        
        if file_extension.lower() in str("pdf").lower():
            print("PDF file request")
            return send_file(
                file_path,
                mimetype='application/pdf'
            )
        elif file_extension.lower() in str("png, jpg,jpeg").lower():
            print("Image file request")
            mimetype, _ = mimetypes.guess_type(file_extension)
            return send_file(
                file_path,
                mimetype=mimetype
            )
        elif file_extension.lower() in str("xlsx").lower():
            print("Excel file request")
            return send_file(
                file_path,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif file_extension.lower() in str("csv").lower():
            print("CSV file request")
            return send_file(
                file_path,
                mimetype='text/csv'
            )
        elif file_extension.lower() in str("docx").lower():
            print("Doc file request")
            return send_file(
                file_path,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            print("Unknow file type")
            return send_file(file_path, as_attachment=True)
        
    return MSG_NOTIFY_FILE_NOT_FOUND, 404

@app.route('/getFolderTree', methods=["GET"])
def getFolderTree():
    response = {}
    response["tree"] = buildFolderTree(PATH_TO_DATABASE, {})
    return json.dumps(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2234)
