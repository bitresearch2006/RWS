from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
import os
from db_handler import init_db, get_or_create_api_key

app = Flask(__name__)
app.secret_key = "supersecretkey"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""


google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_url="/google_callback",
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    dob = request.form['dob']
    phone1 = request.form['phone1']
    phone2 = request.form['phone2']

    if phone1 != phone2:
        flash('Phone numbers do not match', 'error')
        return redirect(url_for('index'))

    flash('Registration successful!', 'success')
    return redirect(url_for('index'))

@app.route("/google_callback")
def google_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "error")
        return redirect(url_for("index"))

    info = resp.json()
    email = info.get("email")

    if not email:
        flash("No email found in Google response.", "error")
        return redirect(url_for("index"))

    session['email'] = email
    session['api_key'] = get_or_create_api_key(email)
    return redirect(url_for("dashboard"))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash("Please login first.", "error")
        return redirect(url_for("index"))
    return render_template("dashboard.html", email=session['email'], api_key=session['api_key'])

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()  # Ensure DB and table exist
    app.run(debug=True)
