from flask import Flask, request, jsonify
import threading
import logging
import os
import importlib.util
import sys
import traceback
import uuid
import argparse
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

# ✅ Parse command-line arguments
parser = argparse.ArgumentParser(description="Flask Server with Multiple External Folders")
parser.add_argument("port", type=int, help="Port number to run the server")
parser.add_argument("config_file", type=str, help="Path to the configuration file")
args = parser.parse_args()

app = Flask(__name__)

requests_threads = {}  # Tracks running threads
responses = {}  # Stores request results
function_map = {}  # Stores loaded functions
lock = threading.Lock()  # Thread safety lock

# ✅ Logging setup
logging.basicConfig(filename=f'RWS_log_{args.port}.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_status(message):
    logging.debug(message)
    print(message)

# ✅ Read external folder paths from the configuration file
def read_external_folders(config_file):
    if not os.path.exists(config_file):
        log_status(f"❌ Error: Configuration file '{config_file}' not found.")
        exit(1)

    valid_paths = []
    with open(config_file, "r") as file:
        for line in file:
            folder_path = os.path.abspath(line.strip())  # Convert to absolute path
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                valid_paths.append(folder_path)
            else:
                log_status(f"⚠️ Invalid path in config file: {folder_path}")

    if not valid_paths:
        log_status("❌ Error: No valid external folders found in configuration file.")
        exit(1)

    return valid_paths

EXTERNAL_FOLDERS = read_external_folders(args.config_file)

# ✅ Load functions from external Python files
def preload_functions():
    def load_functions_from_directory(directory):
        for root, _, files in os.walk(directory):  
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py"]:
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        for attr in dir(module):
                            if callable(getattr(module, attr)) and not attr.startswith("_"):
                                function_map[attr] = getattr(module, attr)
                        log_status(f"✅ Loaded module: {module_name}, functions: {list(function_map.keys())}")
                    except Exception:
                        log_status(f"⚠️ Error loading module {module_name}: {traceback.format_exc()}")

    for folder in EXTERNAL_FOLDERS:
        log_status(f"🔍 Scanning folder: {folder}")
        load_functions_from_directory(folder)

preload_functions()

# ✅ Function Execution
def process_request(service_name, sub_json):
    log_status(f"🛠️ Processing function '{service_name}' with input: {sub_json}")
    if service_name in function_map:
        try:
            result = function_map[service_name](**sub_json)
            log_status(f"✅ Function '{service_name}' executed successfully. Result: {result}")
            return {"status": "SUCCESS", "data": result}
        except Exception as e:
            error_message = str(e)
            log_status(f"❌ Error executing function '{service_name}': {traceback.format_exc()}")
            return {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR", "details": error_message}
    log_status(f"⚠️ Function '{service_name}' not found.")
    return {"status": "ERROR", "error_reason": "FUNCTION_NOT_FOUND"}

# ✅ Handle Asynchronous Requests
def handle_request(request_id, service_name, sub_json, request_type, mail_id=None, phone_no=None):
    try:
        response = process_request(service_name, sub_json)
        with lock:
            responses[request_id] = response  
        if request_type == "MAIL" and mail_id:
            send_email(mail_id, response)
        elif request_type == "SMS" and phone_no:
            send_sms(phone_no, response)
    except Exception as e:
        with lock:
            responses[request_id] = {"status": "ERROR", "error_reason": str(e)}
    finally:
        with lock:
            if request_id in requests_threads:
                del requests_threads[request_id]

# ✅ Main API Endpoint
@app.route('/web_server', methods=['POST'])
def web_server():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Invalid JSON format"}), 400

    request_id = data.get("request_id", str(uuid.uuid4()))
    service_name = data.get("service_name")
    sub_json = data.get("sub_json")
    request_type = data.get("request_type")
    mail_id = data.get("mail_id")
    phone_no = data.get("phone_no")

    if not service_name or not sub_json or not request_type:
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Missing required fields"}), 400

    with lock:
        if request_id in responses and responses[request_id]["status"] != "IN_PROGRESS":
            return jsonify({"request_id": request_id, **responses[request_id]}), 200
        if request_id in requests_threads:
            return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

    if request_type == "INLINE":
        response = process_request(service_name, sub_json)
        return jsonify({"request_id": request_id, **response}), 200

    with lock:
        responses[request_id] = {"status": "IN_PROGRESS"}
    thread = threading.Thread(target=handle_request, args=(request_id, service_name, sub_json, request_type, mail_id, phone_no), daemon=True)
    thread.start()
    with lock:
        requests_threads[request_id] = thread

    return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

if __name__ == '__main__':
    log_status(f"🚀 Starting server on port {args.port} with external folders: {EXTERNAL_FOLDERS}")
    app.run(host='0.0.0.0', port=args.port, debug=False)  # Set debug to False for production
