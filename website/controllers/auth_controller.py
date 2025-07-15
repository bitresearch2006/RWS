from flask import Blueprint, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, UserMixin
from flask_dance.contrib.google import google

auth_bp = Blueprint("auth", __name__)

class User(UserMixin):
    def __init__(self, id_, name, email):
        self.id = str(id_)
        self.name = name
        self.email = email

users = {}

@auth_bp.route("/login")
def login():
    return redirect(url_for("google.login"))

@auth_bp.route("/login/google/authorized")
def authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info", 403

    user_info = resp.json()
    session["profile_pic"] = user_info.get("picture")
    user = User(user_info["id"], user_info["name"], user_info["email"])
    users[user.id] = user
    login_user(user)
    flash("✅ Login successful!")
    return redirect(url_for("service.index"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("🚪 Logged out successfully.")
    return redirect(url_for("service.index"))

def load_user(user_id):
    return users.get(user_id)

def init_login_manager(login_manager):
    login_manager.login_view = "auth.login"
    login_manager.user_loader(load_user)
