from flask import Flask, render_template, url_for
from markupsafe import escape

app = Flask(__name__)

@app.route("/")
def base():
    return "Hello, World!"

@app.route("/<greeting>")
def hello_world(greeting):
    return render_template("index.html",
        cat=url_for('static', filename='cat.jpg'),
        greeting=greeting)