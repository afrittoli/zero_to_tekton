"""Simple flask app."""

from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route("/")
def base():
    """Handles the / route"""
    return "Hello, World!"

@app.route("/<greeting>")
def hello_world(greeting):
    """Handles the /<greeting> route"""
    return render_template("index.html",
                           cat=url_for('static', filename='cat.jpg'),
                           greeting=greeting)
