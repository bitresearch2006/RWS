import requests
import json
import subprocess
import threading
import time


def safe_int_input(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("⚠️ Invalid input! Please enter a valid integer.")

SERVER_URL = "http://{ip}:{port}/web_server"  # IP and Port will be provided dynamically

def send_request(ip, port, user_json, api_key):
    """Send request to the server and handle FUTURE_CALL polling."""
    url = SERVER_URL.format(ip=ip, port=port)
    
    try:
        payload = json.loads(user_json)
        
        payload["X-API-Key"]= api_key  # Use API key
        # Normalize request type to uppercase
        if "request_type" in payload:
            payload["request_type"] = payload["request_type"].strip().upper()
        else:
            print("⚠️ Missing 'request_type'! Request aborted.")
            return
        
        # Validate request type
        if payload["request_type"] not in {"INLINE", "FUTURE_CALL", "MAIL", "SMS"}:
            print(f"⚠️ Invalid request type '{payload['request_type']}'! Request aborted.")
            return
        
        # Ensure function name is case insensitive
        if "service_name" in payload:
            payload["service_name"] = payload["service_name"].lower()
        
        # Ensure email is provided for MAIL request
        if payload["request_type"] == "MAIL":
            if "mail_id" not in payload or not payload["mail_id"].strip():
                while True:
                    payload["mail_id"] = input("🔹 Enter Email for MAIL request: ").strip()
                    if payload["mail_id"]:
                        break
                    print("⚠️ Email is required for MAIL requests!")
        
        # Ensure phone number is provided for SMS request
        if payload["request_type"] == "SMS":
            if "phone_no" not in payload or not payload["phone_no"].strip():
                while True:
                    payload["phone_no"] = input("🔹 Enter Phone Number for SMS request: ").strip()
                    if payload["phone_no"]:
                        break
                    print("⚠️ Phone number is required for SMS requests!")
        
        response = requests.post(url, json=payload)
        response_json = response.json()
        print("\n✅ Response:", json.dumps(response_json, indent=4))
        
        if payload.get("request_type") == "FUTURE_CALL" and response_json.get("status") == "IN_PROGRESS":
            request_id = response_json.get("request_id")
            print(f"🔄 Request ID {request_id} is processing. Checking for results...")
            check_future_call_result(ip, port, request_id, payload["service_name"], payload["sub_json"])
    
    except json.JSONDecodeError:
        print("⚠️ Invalid JSON format! Please provide valid JSON.")
    except requests.exceptions.RequestException as e:
        print("\n⚠️ Error:", e)

def check_future_call_result(ip, port, request_id, service_name, sub_json):
    """Poll the server for FUTURE_CALL result until it's ready."""
    url = SERVER_URL.format(ip=ip, port=port)
    while True:
        try:
            payload = {
                "request_id": request_id,
                "service_name": service_name,
                "sub_json": sub_json,
                "request_type": "FUTURE_CALL"
            }
            response = requests.post(url, json=payload)
            response_json = response.json()
            
            if response_json.get("status") == "SUCCESS":
                print("\n✅ Final Result:", json.dumps(response_json, indent=4))
                break
            elif response_json.get("status") == "IN_PROGRESS":
                print("🔄 Still processing... Checking again in 5 seconds.")
            else:
                print("\n⚠️ Unexpected Response:", response_json)
                break
        except requests.exceptions.RequestException as e:
            print("\n⚠️ Error:", e)
            break
        
        import time
        time.sleep(5)
        
def call_subprocess(args):
    subprocess.run(['python', '../main/server.py'] + args )       

def main():
    """Client menu for sending requests."""
    ip = input("🔹 Enter server IP address: ").strip()
    port = input("🔹 Enter server port: ").strip()
    if not port.isdigit():
        print("⚠️ Invalid port! Please enter a valid number.")
        return
    port = int(port)
    
    api_key = input("🔹 Enter your API key: ").strip()
    
    while True:
        print("\n🔹 Enter your request JSON format:")
        print('{"request_type": "INLINE/FUTURE_CALL/MAIL/SMS", "service_name": "add/sp/...", "sub_json": {...}}')
        user_json = input("🔹 Enter JSON request: ").strip()
        if not user_json:
            print("⚠️ No input provided! Please enter a valid JSON request.")
            continue
        send_request(ip, port, user_json, api_key)

if __name__ == "__main__":
    args = ['--diagnostics', '5000', '../test/stub/services_path.txt','../test/stub/api_database.db']
    thread = threading.Thread(target=call_subprocess, args=(args,))
    thread.start()
    time.sleep(5)
    main()
    thread.join()   # Wait for the subprocess to complete if needed

