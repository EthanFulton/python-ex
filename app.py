# personal note: use
#   source /projects/flask-example/.venv/bin/activate
# for switching to venv to pip install modules in terminal

from flask import Flask, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from io import BytesIO
import json, os, pyotp, qrcode, base64

load_dotenv()

app = Flask(__name__)
# get secret key to use for hashing
app.secret_key = os.getenv("SECRET-KEY")

# Ensure data folder exists
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
POSTS_FILE = os.path.join(DATA_DIR, "posts.json")

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    if "user" in session:
        return redirect("/thread")

    return '''
    <h1>You are not signed into an account</h1>
    <p>Please choose an option below:</p>

    <a href="/login">
        <button style="padding:10px 20px; margin:5px;">Login</button>
    </a>

    <a href="/register">
        <button style="padding:10px 20px; margin:5px;">Register</button>
    </a>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_json(USERS_FILE, {})
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return "User already exists"

        # gen secret
        secret = pyotp.random_base32()

        users[username] = {
            "password_hash": generate_password_hash(password),
            "otp_secret": secret
        }
        save_json(USERS_FILE, users)

        # creating qr code

        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name="SimpleForumApp")

        img = qrcode.make(uri)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # returning qr code to user
        return f'''
        <h3>Registration Successful</h3>
        <p>Scan this QR code with Google Authenticator or Microsoft Authenticator:</p>

        <img src="data:image/png;base64,{qr_base64}" />
        ``

        <p>If you cannot scan, manually enter this code:</p>
        <b>{secret}</b>

        <br><br>
        <a href="/login">
        <button style="padding:10px 20px; margin:5px;">Go to Login</button>
        </a>
        '''


    return '''
    <h2>Register</h2>

    <form method="POST">
        Username: <input name="username"><br><br>

        Password: <input id="password" name="password" type="password" onkeyup="checkStrength()"><br>
        <div id="strength" style="font-weight:bold;"></div><br>

        <button>Register</button>
    </form>

    <script>
    function checkStrength() {
        let password = document.getElementById("password").value;
        let strengthText = document.getElementById("strength");

        let strength = 0;

        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;

        if (password.length === 0) {
            strengthText.innerHTML = "";
            return;
        }

        if (strength <= 2) {
            strengthText.innerHTML = "Weak - A strong password is atleast 8 characters, includes lowercase (a-z), uppercase (A-Z), numbers (0-9), and characters (!?@#...)";
            strengthText.style.color = "red";
        } else if (strength == 3 || strength == 4) {
            strengthText.innerHTML = "Medium - A strong password is atleast 8 characters, includes lowercase (a-z), uppercase (A-Z), numbers (0-9), and characters (!?@#...)";
            strengthText.style.color = "orange";
        } else {
            strengthText.innerHTML = "Strong - Great!";
            strengthText.style.color = "green";
        }
    }
    </script>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_json(USERS_FILE, {})
        username = request.form['username']
        password = request.form['password']

        if username not in users:
            return "Invalid username"

        if not check_password_hash(users[username]["password_hash"], password):
            return "Invalid password"

        # store temp user for 2fa
        session['temp_user'] = username
        return redirect('/verify')

    return '''
    <form method="POST">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <button>Login</button>
    </form>
    '''

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    # keep someone not logged in from going straight to /verify page
    if 'temp_user' not in session:
        return redirect('/login')

    users = load_json(USERS_FILE, {})
    username = session['temp_user']
    secret = users[username]["otp_secret"]

    import pyotp
    totp = pyotp.TOTP(secret)

    if request.method == 'POST':
        code = request.form['code']

        if totp.verify(code, valid_window=1):
            # login succeeded
            session.pop('temp_user')
            session['user'] = username
            return redirect('/thread')
        else: # login failed
            return '''
            <h3>Invalid code</h3>
            <br><br>
            <a href="/login">
            <button style="padding:10px 20px; margin:5px;">Retry Login</button>
            </a>
            '''

    return '''
    <h3>Enter 2FA Code</h3>
    <form method="POST">
        Code: <input name="code"><br>
        <button>Verify</button>
    </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/thread', methods=['GET', 'POST'])
def thread():
    if "user" not in session:
        return redirect('/login')

    posts = load_json(POSTS_FILE, [])

    if request.method == 'POST':
        message = request.form['message']
        posts.append({"user": session["user"], "message": message})
        save_json(POSTS_FILE, posts)

    html = "<h1>Message Board</h1>"
    html += "<form method='POST'>Message: <input name='message'><button>Post</button></form><br><br>"

    for p in posts:
        html += f"<b>{p['user']}:</b> {p['message']}<br>"

    html += "<br><a href='/logout'>Logout</a>"
    return html

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0')