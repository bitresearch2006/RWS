from flask import Flask
from flask_login import LoginManager
from flask_dance.contrib.google import make_google_blueprint
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import app configuration and blueprints
from config import Config
from controllers.auth_controller import auth_bp, init_login_manager
from controllers.service_controller import service_bp

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Setup Login Manager
login_manager = LoginManager(app)
init_login_manager(login_manager)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(service_bp)

# Google OAuth Blueprint
google_bp = make_google_blueprint(
    client_id=Config.GOOGLE_OAUTH_CLIENT_ID,
    client_secret=Config.GOOGLE_OAUTH_CLIENT_SECRET,
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_url="/login/google/authorized",
    reprompt_consent=True  # Forces Gmail account selector
)
app.register_blueprint(google_bp, url_prefix="/login")

# Run the app
if __name__ == "__main__":
    app.run(
        debug=True,
        ssl_context=("cert/cert.pem", "cert/key.pem"),  # 👈 Enable HTTPS locally
        host="127.0.0.1",
        port=5000
    )
