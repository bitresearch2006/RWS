import sqlite3
import secrets

DB_NAME = "api_database.db"

# Create table if not exists
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                api_key TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

# Generate new API key
def generate_api_key():
    return secrets.token_hex(64)

# Get or create API key by email
def get_or_create_api_key(email):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM api_keys WHERE email = ?", (email,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            api_key = generate_api_key()
            cursor.execute("INSERT INTO api_keys (email, api_key) VALUES (?, ?)", (email, api_key))
            conn.commit()
            return api_key
