# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # fallback if not in .env
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "bitresearch2006")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
