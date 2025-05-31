from flask import Flask, render_template, abort
import requests
import markdown
import logging
import time
from config import GITHUB_USERNAME, GITHUB_TOKEN

app = Flask(__name__)

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()  # Automatically handles console output
    ]
)

logging.info("🚀 Starting GitHub Services Flask App")


def get_repositories():
    start = time.time()
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    duration = time.time() - start

    if response.status_code == 200:
        logging.info(f"✅ Repositories fetched successfully in {duration:.2f} sec")
        return response.json()
    else:
        logging.error(f"❌ Failed to fetch repositories in {duration:.2f} sec: {response.status_code} - {response.text}")
        return []


def get_readme(repo_name):
    start = time.time()
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/readme"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    duration = time.time() - start

    if response.status_code == 200:
        logging.info(f"📘 README fetched for {repo_name} in {duration:.2f} sec")
        return response.text
    else:
        logging.warning(f"⚠️ No README found for {repo_name} in {duration:.2f} sec. Status: {response.status_code}")
        return None


@app.route('/')
def index():
    route_start = time.time()
    logging.info("🌐 Accessed / (home)")

    repositories = get_repositories()
    services = []
    for repo in repositories:
        readme = get_readme(repo['name'])
        if readme:
            services.append(repo['name'])

    route_duration = time.time() - route_start
    logging.info(f"📄 Rendered index with {len(services)} services in {route_duration:.2f} sec")
    return render_template('index.html', services=services)


@app.route('/service/<repo_name>')
def service(repo_name):
    route_start = time.time()
    logging.info(f"🌐 Accessed /service/{repo_name}")

    readme = get_readme(repo_name)
    if readme:
        html_content = markdown.markdown(readme)
        duration = time.time() - route_start
        logging.info(f"📄 Rendered /service/{repo_name} in {duration:.2f} sec")
        return render_template('service.html', service_name=repo_name, content=html_content)
    else:
        duration = time.time() - route_start
        logging.warning(f"❌ README not found for {repo_name}, failed to render in {duration:.2f} sec")
        abort(404)


if __name__ == '__main__':
    app.run(debug=True)
