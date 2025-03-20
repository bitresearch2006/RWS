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
import re
import uuid

app = Flask(__name__)

requests_threads = {}
responses = {}
function_map = {}
lock = threading.Lock()

logging.basicConfig(filename='RWS_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_status(message):
    logging.debug(message)

def read_external_folders():
    """Read external folder paths from a text file."""
    path_file = os.path.join(os.path.dirname(__file__), 'external_paths.txt')
    if os.path.exists(path_file):
        with open(path_file, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    return []

EXTERNAL_FOLDERS = read_external_folders()

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def is_valid_phone(phone):
    phone_regex = r'^\+[1-9]\d{1,14}$'
    return re.match(phone_regex, phone)

def preload_functions():
    current_folder = os.path.dirname(os.path.abspath(__file__))
    for folder in EXTERNAL_FOLDERS:
        if folder not in sys.path:
            sys.path.append(folder)

    def load_functions_from_directory(directory):
        for root, _, files in os.walk(directory):  
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py", os.path.basename(__file__)]:
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.relpath(module_path, current_folder))[0].replace(os.sep, ".")
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        for attr in dir(module):
                            if callable(getattr(module, attr)) and not attr.startswith("_"):
                                function_map[attr] = getattr(module, attr)
                    except Exception:
                        log_status(f"⚠️ Error loading module {module_name}: {traceback.format_exc()}")

    load_functions_from_directory(current_folder)
    for folder in EXTERNAL_FOLDERS:
        if os.path.exists(folder):
            load_functions_from_directory(folder)

preload_functions()

def process_request(service_name, sub_json):
    log_status(f"Processing function '{service_name}' with input: {sub_json}")
    log_status(f"Available functions: {list(function_map.keys())}")
    if service_name in function_map:
        try:
            result = function_map[service_name](**sub_json)
            return {"status": "SUCCESS", "data": result}
        except Exception:
            log_status(f"Error executing function '{service_name}': {traceback.format_exc()}")
            return {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR"}
    else:
        return {"status": "ERROR", "error_reason": "FUNCTION_NOT_FOUND"}

def handle_request(request_id, service_name, sub_json, request_type, mail_id=None, phone_no=None):
    try:
        response = process_request(service_name, sub_json)
        with lock:
            responses[request_id] = response
        if request_type == "MAIL":
            send_email(mail_id, response)
        elif request_type == "SMS":
            send_sms(phone_no, response)
    except Exception:
        log_status(f"Error handling request '{request_id}': {traceback.format_exc()}")
        with lock:
            responses[request_id] = {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR"}
    finally:
        with lock:
            requests_threads.pop(request_id, None)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def send_sms(phone_no, response):
    log_status(f"Sending SMS to {phone_no} with response: {response}")
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        log_status("Twilio credentials are missing!")
        return
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(body=f"Response: {response}", from_=TWILIO_PHONE_NUMBER, to=phone_no)
        log_status(f"SMS sent successfully: {message.sid}")
    except Exception as e:
        log_status(f"Error sending SMS: {e}")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_email(mail_id, response):
    log_status(f"Sending email to {mail_id} with response: {response}")
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        log_status("Email credentials are missing!")
        return
    try:
        msg = MIMEText(f"Response: {response}")
        msg["Subject"] = "Server Response"
        msg["From"] = SENDER_EMAIL
        msg["To"] = mail_id
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, mail_id, msg.as_string())
        log_status(f"Email sent successfully to {mail_id}")
    except Exception as e:
        log_status(f"Error sending email: {e}")

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
    thread = threading.Thread(target=handle_request, args=(request_id, service_name, sub_json, request_type, mail_id, phone_no))
    thread.start()
    with lock:
        requests_threads[request_id] = thread
    return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
