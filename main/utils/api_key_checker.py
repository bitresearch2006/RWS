# utils/api_key_checker.py
import sqlite3
from utils.logger import log_status

def is_api_key_valid(api_key, database_path, logger):
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE api_key = ?", (api_key,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        log_status(logger, f"Database error: {str(e)}", "error")
        return False
