from flask import Flask, request, jsonify
import threading
import logging
import os
import importlib.util
import sys
import traceback
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
import uuid
import re

app = Flask(__name__)

requests_threads = {}  # Tracks running threads
responses = {}  # Stores request results
function_map = {}  # Stores loaded functions
lock = threading.Lock()  # Thread safety lock

# ✅ Logging setup
logging.basicConfig(filename='RWS_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_status(message):
    logging.debug(message)
    print(message)  # ✅ Prints to console for debugging

# ✅ Email & Phone Validation
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))

def is_valid_phone(phone):
    phone_regex = r'^\+[1-9]\d{1,14}$'  # International format (+1234567890)
    return bool(re.match(phone_regex, phone))

# ✅ Load external function directories from a file
def read_external_folders():
    path_file = os.path.join(os.path.dirname(__file__), 'external_paths.txt')
    valid_paths = []
    if os.path.exists(path_file):
        with open(path_file, 'r') as file:
            for line in file:
                folder_path = line.strip()
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    valid_paths.append(folder_path)
                else:
                    log_status(f"⚠️ Invalid path: {folder_path}")
    return valid_paths

EXTERNAL_FOLDERS = read_external_folders()

# ✅ Preload functions from external Python files
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
        if os.path.exists(folder):
            log_status(f"🔍 Scanning folder: {folder}")
            load_functions_from_directory(folder)

preload_functions()

# ✅ Function Execution
def process_request(service_name, sub_json):
    log_status(f"🛠️ Processing function '{service_name}' with input: {sub_json}")
    log_status(f"📌 Available functions: {list(function_map.keys())}")

    if service_name in function_map:
        try:
            result = function_map[service_name](**sub_json)
            log_status(f"✅ Function '{service_name}' executed successfully. Result: {result}")
            return {"status": "SUCCESS", "data": result}
        except Exception:
            log_status(f"❌ Error executing function '{service_name}': {traceback.format_exc()}")
            return {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR"}
    
    log_status(f"⚠️ Function '{service_name}' not found.")
    return {"status": "ERROR", "error_reason": "FUNCTION_NOT_FOUND"}

# ✅ Main API Endpoint
@app.route('/web_server', methods=['POST'])
def web_server():
    """Handles incoming requests."""
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

    # ✅ Validate email and phone
    if request_type == "MAIL" and (not mail_id or not is_valid_email(mail_id)):
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Invalid or missing email"}), 400

    if request_type == "SMS" and (not phone_no or not is_valid_phone(phone_no)):
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Invalid or missing phone number"}), 400

    # ✅ FUTURE_CALL Handling: Check if result already exists
    with lock:
        if request_id in responses and responses[request_id]["status"] != "IN_PROGRESS":
            return jsonify({"request_id": request_id, **responses[request_id]}), 200  # Return stored response

    if request_type == "INLINE":
        response = process_request(service_name, sub_json)
        return jsonify({"request_id": request_id, **response}), 200

    with lock:
        responses[request_id] = {"status": "IN_PROGRESS"}

    # ✅ Start background thread
    thread = threading.Thread(target=handle_request, args=(request_id, service_name, sub_json, request_type, mail_id, phone_no), daemon=True)
    thread.start()

    with lock:
        requests_threads[request_id] = thread

    log_status(f"🟢 Started thread for request: {request_id}")
    return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

# ✅ Handle Asynchronous Requests
def handle_request(request_id, service_name, sub_json, request_type, mail_id=None, phone_no=None):
    """Handles execution of FUTURE_CALL requests asynchronously."""
    log_status(f"🚀 Executing handle_request for request_id: {request_id}")

    try:
        response = process_request(service_name, sub_json)
        with lock:
            responses[request_id] = response  # ✅ Store result for FUTURE_CALL
            log_status(f"✅ Request {request_id} completed with response: {response}")

        if request_type == "MAIL" and mail_id:
            send_email(mail_id, response)
        elif request_type == "SMS" and phone_no:
            send_sms(phone_no, response)

    except Exception:
        log_status(f"❌ Error handling request '{request_id}': {traceback.format_exc()}")
        with lock:
            responses[request_id] = {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR"}

    finally:
        with lock:
            requests_threads.pop(request_id, None)  # ✅ Cleanup thread
        log_status(f"🔴 Thread cleaned up for request: {request_id}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
