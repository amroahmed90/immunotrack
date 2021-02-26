import sqlite3
from helpers import login_required
from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from tempfile import mkdtemp

# setting up the flask application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# setup the connection to the database
conn = sqlite3.connect("immunotrack.db")

# default route


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health_workers")
def health_workers():
    return render_template("health_workers.html")


@app.route("/public_access")
def public_access():
    return render_template("public_access.html")


@app.route("/about")
def about():
    return render_template("about.html")


# setup a cursor on which you'll execute sqlite commands
#c = conn.cursor()
# execute your commands
# This is how to insert (question marks as placeholders and tuples)
## c.execute("INSERT INTO employees VALUES (?,?,?)", (emp1.first, emp1.last, emp1.pay))
# Another way to avoid SQL injection attacks is like the following (using colons and dictionary)
## c.execute("INSERT INTO employees VALUES (:first, :last, :pay)", {'first' : emp1.first, 'last' : emp1.last, 'pay' : emp1.pay})

# after quering a select query, apply these commands to fetch the data
# c.fetchone() # output is tuple
# c.fetchmeny(3) # output is a list of tuples
# c.fetchall() #output is a list of tuples

# commit these commands
# conn.commit()
# close the connection at the end
# conn.close()
