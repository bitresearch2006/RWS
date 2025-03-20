import requests
import json

# ✅ Default Flask server URL
SERVER_URL = "http://127.0.0.1:5000/web_server"

# ✅ Function to ensure valid integer input
def safe_int_input(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("⚠️ Invalid input! Please enter a valid integer.")

# ✅ System-defined parameters for known functions
DEFAULT_PARAMS = {
    "sp": lambda: {"symbol": input("  ➤ Enter stock symbol: ").strip().upper()},
    "pc": lambda: {"symbol": input("  ➤ Enter stock symbol: ").strip().upper()},
    "add": lambda: {"a": safe_int_input("  ➤ Enter first number (a): "), "b": safe_int_input("  ➤ Enter second number (b): ")},
    "sub": lambda: {"a": safe_int_input("  ➤ Enter first number (a): "), "b": safe_int_input("  ➤ Enter second number (b): ")},
    "mul": lambda: {"a": safe_int_input("  ➤ Enter first number (a): "), "b": safe_int_input("  ➤ Enter second number (b): ")},
    "div": lambda: {"a": safe_int_input("  ➤ Enter numerator (a): "), "b": safe_int_input("  ➤ Enter denominator (b): ")}
}

def send_request(service, req_type, params, email=None, phone=None):
    """Send request to the server and handle FUTURE_CALL polling."""
    payload = {
        "service_name": service,
        "sub_json": params,
        "request_type": req_type
    }
    if email:
        payload["mail_id"] = email
    if phone:
        payload["phone_no"] = phone

    try:
        response = requests.post(SERVER_URL, json=payload)
        response_json = response.json()
        print("\n✅ Response:", json.dumps(response_json, indent=4))

        # ✅ Handle FUTURE_CALL polling
        if req_type == "FUTURE_CALL" and response_json.get("status") == "IN_PROGRESS":
            request_id = response_json.get("request_id")
            print(f"🔄 Request ID {request_id} is processing. Checking for results...")
            check_future_call_result(request_id, service, params)  # ✅ Pass required fields
    
    except requests.exceptions.RequestException as e:
        print("\n⚠️ Error:", e)

def check_future_call_result(request_id, service_name, sub_json):
    """Poll the server for FUTURE_CALL result until it's ready."""
    while True:
        try:
            payload = {
                "request_id": request_id,
                "service_name": service_name,  # ✅ Include service_name
                "sub_json": sub_json,  # ✅ Include sub_json (parameters)
                "request_type": "FUTURE_CALL"
            }
            response = requests.post(SERVER_URL, json=payload)
            response_json = response.json()

            if response_json.get("status") == "SUCCESS":
                print("\n✅ Final Result:", json.dumps(response_json, indent=4))
                break  # ✅ Stop polling when result is ready
            
            elif response_json.get("status") == "IN_PROGRESS":
                print("🔄 Still processing... Checking again in 5 seconds.")
            
            else:
                print("\n⚠️ Unexpected Response:", response_json)
                break
            
        except requests.exceptions.RequestException as e:
            print("\n⚠️ Error:", e)
            break
        
        import time
        time.sleep(5)  # ✅ Wait before polling again

def main():
    """Client menu for sending requests."""
    while True:
        req_type = input("\n🔹 Request type (INLINE, FUTURE_CALL, MAIL, SMS): ").strip().upper()
        if req_type not in {"INLINE", "FUTURE_CALL", "MAIL", "SMS"}:
            print("⚠️ Invalid request type! Try again.")
            continue

        service = input("🔹 Function name (add, sub, mul, div, sp, pc): ").strip()
        if service not in DEFAULT_PARAMS:
            print("⚠️ Invalid function name! Try again.")
            continue

        params = DEFAULT_PARAMS[service]()  # ✅ Auto-generate parameters

        email, phone = None, None

        if req_type == "MAIL":
            while not email:
                email = input("🔹 Email (required for MAIL): ").strip()
                if not email:
                    print("⚠️ Email is required for MAIL requests!")

        if req_type == "SMS":
            while not phone:
                phone = input("🔹 Phone (required for SMS): ").strip()
                if not phone:
                    print("⚠️ Phone number is required for SMS requests!")

        send_request(service, req_type, params, email, phone)  # ✅ Send request

if __name__ == "__main__":
    main()
