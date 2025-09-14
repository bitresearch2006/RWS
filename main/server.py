# server.py
from flask import Flask, request, jsonify
import threading
import logging
import os
import importlib.util
import sys
import traceback
import uuid
import argparse
import sqlite3

from utils.logger import setup_logger, log_status
from utils.config_loader import read_external_folders
from utils.function_loader import preload_functions
from utils.api_key_checker import is_api_key_valid
from utils.request_handler import handle_request, process_request
from utils.state_manager import ThreadSafeStore

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Flask Server with Multiple External Folders")
parser.add_argument("port", type=int, help="Port number to run the server")
parser.add_argument("config_file", type=str, help="Path to the configuration file")
parser.add_argument("database_path", type=str, help="Path to the SQLite database file")
parser.add_argument("--diagnostics", action="store_true", help="Enable diagnostics logging")
args = parser.parse_args()

# Setup logger
log_file = f'RWS_log_{args.port}.log'
logger = setup_logger(log_file, args.diagnostics)

# Database path and application setup
DATABASE_PATH = args.database_path
app = Flask(__name__)
state = ThreadSafeStore()

# Load configuration and functions
EXTERNAL_FOLDERS = read_external_folders(args.config_file, logger)
preload_functions(EXTERNAL_FOLDERS, logger)

@app.route('/web_server', methods=['POST'])
def web_server():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Invalid JSON format"}), 400

    api_key = data.get("X-API-Key")
    if not api_key or not is_api_key_valid(api_key, DATABASE_PATH, logger):
        return jsonify({"status": "UNAUTHORIZED", "error": "Invalid or missing API key"}), 401

    request_id = data.get("request_id", str(uuid.uuid4()))
    service_name = data.get("service_name")
    sub_json = data.get("sub_json")
    request_type = data.get("request_type")
    mail_id = data.get("mail_id")
    phone_no = data.get("phone_no")

    if not service_name or not sub_json or not request_type:
        return jsonify({"status": "INVALID_ARGUMENT", "error": "Missing required fields"}), 400

    existing_response = state.get_response(request_id)
    if existing_response and existing_response.get("status") != "IN_PROGRESS":
        return jsonify({"request_id": request_id, **existing_response}), 200
    if state.is_in_progress(request_id):
        return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

    if request_type == "INLINE":
        response = process_request(service_name, sub_json, logger)
        return jsonify({"request_id": request_id, **response}), 200

    state.set_response(request_id, {"status": "IN_PROGRESS"})
    thread = threading.Thread(target=handle_request, args=(request_id, service_name, sub_json, request_type, mail_id, phone_no, logger, state), daemon=True)
    thread.start()
    state.set_thread(request_id, thread)

    return jsonify({"status": "IN_PROGRESS", "request_id": request_id}), 202

if __name__ == '__main__':
    log_status(logger, f"🚀 Starting server on port {args.port} with external folders: {EXTERNAL_FOLDERS}")
    app.run(host='0.0.0.0', port=args.port, debug=args.diagnostics)
