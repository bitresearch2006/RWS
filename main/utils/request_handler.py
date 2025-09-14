# utils/request_handler.py
import threading
import traceback
from utils.logger import log_status

def process_request(service_name, sub_json, logger):
    log_status(logger, f"🛠️ Processing function '{service_name}' with input: {sub_json}")
    from utils.function_loader import function_map

    if service_name in function_map:
        try:
            result = function_map[service_name](**sub_json)
            log_status(logger, f"✅ Function '{service_name}' executed successfully. Result: {result}")
            return {"status": "SUCCESS", "data": result}
        except Exception as e:
            error_message = str(e)
            log_status(logger, f"❌ Error executing function '{service_name}': {traceback.format_exc()}", "error")
            return {"status": "ERROR", "error_reason": "FUNCTION_EXECUTION_ERROR", "details": error_message}

    log_status(logger, f"⚠️ Function '{service_name}' not found.", "warning")
    return {"status": "ERROR", "error_reason": "FUNCTION_NOT_FOUND"}

def handle_request(request_id, service_name, sub_json, request_type, mail_id=None, phone_no=None, logger=None, state=None):
    try:
        response = process_request(service_name, sub_json, logger)
        state.set_response(request_id, response)

        if request_type == "MAIL" and mail_id:
            # Placeholder for email sending
            log_status(logger, f"📧 Email sent to {mail_id} with response: {response}")
        elif request_type == "SMS" and phone_no:
            # Placeholder for SMS sending
            log_status(logger, f"📱 SMS sent to {phone_no} with response: {response}")

    except Exception as e:
        state.set_response(request_id, {"status": "ERROR", "error_reason": str(e)})
    finally:
        state.remove_thread(request_id)
