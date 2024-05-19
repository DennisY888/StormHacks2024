import os

import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        name = request.form.get("person_name")
        if not name:
            return redirect("/")
        try:
            reps = int(request.form.get("reps"))
            score = int(request.form.get("score"))
        except ValueError:
            return redirect("/")

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, reps, score) VALUES (?, ?, ?);", (name, reps, score))
            conn.commit()

        return redirect("/")

    else:
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT * FROM users ORDER BY reps DESC").fetchall()
        return render_template("index.html", users=rows)
    

    

@app.route("/remove", methods=["POST"])
def remove():
    id = request.form.get("id")
    if id:
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (id))
            conn.commit()
    return redirect("/")

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

if __name__ == "__main__":
    app.run(debug=True)