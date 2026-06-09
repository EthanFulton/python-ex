from flask import Flask, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import json, os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # replace later

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

        users[username] = {
            "password_hash": generate_password_hash(password)
        }
        save_json(USERS_FILE, users)
        return "Registered! Go to /login"

    return '''
    <form method="POST">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <button>Register</button>
    </form>
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

        session['user'] = username
        return redirect('/thread')

    return '''
    <form method="POST">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <button>Login</button>
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
