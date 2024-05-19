from functools import wraps
import os

import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import subprocess
# from push_ups import rep_count



# Configure application
app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)





def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("name") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function




@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response






@app.route("/push", methods=["POST"])
def push():
    try:
        # Replace 'push_ups.py' with the correct path to your Python script
        subprocess.run(["python", "push_ups.py"], check=True)
        return redirect("/leaderboard")
    except subprocess.CalledProcessError as e:
        return render_template("apology.html")
    



@app.route("/squat", methods=["POST"])
def squat():
    try:
        # Replace 'push_ups.py' with the correct path to your Python script
        subprocess.run(["python", "squats.py"], check=True)
        return redirect("/leaderboard")
    except subprocess.CalledProcessError as e:
        return render_template("apology.html")










@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("apology.html")

        elif not request.form.get("password"):
            return render_template("apology.html")


        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()


        if len(rows) != 1 or not check_password_hash(rows[0][4], request.form.get("password")):
            return render_template("apology.html")

        session["name"] = rows[0][1]
        
        with open("rep_count.txt", "w") as file:
            file.write(str(session["name"]))

        return redirect("/leaderboard")

    else:
        return render_template("login.html")
    



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if not request.form.get("register_username"):
            return render_template("apology.html")

        elif not request.form.get("register_password"):
            return render_template("apology.html")


        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM users WHERE username = ?", (request.form.get("register_username"),)).fetchall()


        if len(rows) != 0:
            return render_template("failed_register.html")
        

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            rows = cursor.execute("INSERT INTO users (username, reps, score, password, total_reps) VALUES (?, ?, ?, ?, ?)", (request.form.get("register_username"), 0, 0, generate_password_hash(request.form.get("register_password")), 0))
            conn.commit()


        return redirect("/login")

    else:
        return render_template("register.html")


    

@app.route("/logout")
@login_required
def logout():
    with open("rep_count.txt", "w") as file:
        file.write("")
    session.clear()
    return redirect("/login")



@app.route("/")
def index():
    return render_template("index.html")



@app.route("/leaderboard", methods=["GET", "POST"])
@login_required
def leaderboard():

    if request.method == "POST":
        try:
            reps = int(request.form.get("reps"))
            score = int(request.form.get("score"))
        except ValueError:
            return redirect("/")

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            total_reps = cursor.execute("SELECT total_reps FROM users WHERE username = ?", (session["name"],)).fetchone()
            cursor.execute("UPDATE users SET reps = ?, score = ?, total_reps = ? WHERE username = ?;", (reps, score, total_reps[0] + reps, session["name"]))
            conn.commit()

        return redirect("/leaderboard")

    else:

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM users ORDER BY reps DESC;").fetchall()
            total_reps = cursor.execute("SELECT total_reps FROM users WHERE username = ?;", (session["name"],)).fetchone()
            if total_reps is not None:
                return render_template("leaderboard.html", users=rows, coins=total_reps[0])
            else:
                return render_template("leaderboard.html", users=rows, coins=0)

        




@app.route("/remove", methods=["POST"])
@login_required
def remove():
    id = request.form.get("id")
    if id:
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (id))
            conn.commit()
    return redirect("/leaderboard")


if __name__ == "__main__":
    app.run(debug=True)



