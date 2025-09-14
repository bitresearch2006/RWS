from flask import Blueprint, render_template, abort, redirect
from flask_login import current_user
import requests
import markdown
import random
from config import Config

service_bp = Blueprint("service", __name__)

# List of Font Awesome icon classes
ICON_CLASSES = [
    "fa-cogs", "fa-box", "fa-brain", "fa-lightbulb", "fa-tools",
    "fa-desktop", "fa-plug", "fa-vial", "fa-globe", "fa-bolt"
]

def get_repositories():
    url = f"https://api.github.com/users/{Config.GITHUB_USERNAME}/repos"
    headers = {"Authorization": f"token {Config.GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json() if response.ok else []

def get_readme(repo_name):
    url = f"https://api.github.com/repos/{Config.GITHUB_USERNAME}/{repo_name}/readme"
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    return response.text if response.ok else None

@service_bp.route("/")
def root():
    return redirect("/home")

@service_bp.route("/home")
def home():
    return render_template("home.html")

@service_bp.route("/services")
def index():
    repositories = get_repositories()
    services = []

    for repo in repositories:
        if get_readme(repo["name"]):
            icon = random.choice(ICON_CLASSES)
            services.append({
                "name": repo["name"],
                "icon": icon
            })

    return render_template("index.html", services=services, user=current_user)

@service_bp.route("/service/<repo_name>")
def service_detail(repo_name):
    readme = get_readme(repo_name)
    if readme:
        html_content = markdown.markdown(readme)
        return render_template("service.html", service_name=repo_name, content=html_content)
    else:
        abort(404)

@service_bp.route("/contact")
def contact():
    return render_template("contact.html")

@service_bp.route("/about")
def about():
    return render_template("about.html")

@service_bp.route("/guidelines")
def guidelines():
    return render_template("guidelines.html")
