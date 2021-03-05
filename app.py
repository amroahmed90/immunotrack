import sqlite3
from helpers import login_required, apology
from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash


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


# default route
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health_workers")
def health_workers():
    return render_template("health_workers.html")


@app.route("/health_worker_profile", methods=["GET", "POST"])
# @login_required
def health_roker_profile():
    # if the form get submitted
    if request.method == "POST":
        # getting the inputs from the registration form and checking these inputs
        fname = request.form.get("fname")
        if not fname:
            return apology("First name was not provided", "/health_workers")
        mname = request.form.get("mname")
        lname = request.form.get("lname")
        if not lname:
            return apology("Last name was not provided", "/health_workers")
        social_number = request.form.get("social_number")
        if not social_number:
            return apology("Social number was not provided", "/health_workers")
        # checking if this user has registered before using their unique social_number
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE social_number = ?", (social_number,))
            not_registered = len(c.fetchall())
            print(not_registered)
            if not_registered:
                return apology("This social number has been registered before.", "/health_workers")
        hospital = request.form.get("hospital")
        if not hospital:
            return apology("Place of work (hospital name) was not provided", "/health_workers")
        email = request.form.get("email")
        if not email:
            return apology("Email was not provided", "/health_workers")
        # checking if this user has registered before using their unique email
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE email = ?", (email,))
            not_registered = len(c.fetchall())
            print(not_registered)
            if not_registered:
                return apology("This email has been registered before.", "/health_workers")
        password = request.form.get("password")
        if not password:
            return apology("Password was not provided", "/health_workers")
        password_confirmation = request.form.get("password_confirmation")
        if not password_confirmation:
            return apology("Password confirmation name was not provided", "/health_workers")
        # checking if the password input does not match confirmation
        if password != password_confirmation:
            return apology("Password does not match the confirmation", "/health_workers")
        # hashing the passord
        hashed = generate_password_hash(password)
        # sql queries
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id FROM hospitals WHERE hospital_name = ?", (hospital,))
            hospital_id = c.fetchall()
            c.execute("""INSERT INTO health_workers (first_name, middle_name, last_name, social_number, work_hospital_id, email, password_hash)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (fname, mname, lname, social_number, hospital_id[0][0], email, hashed))
            conn.commit()
        return render_template("health_worker_profile.html")
    # if the method was GET
    else:
        return render_template("health_workers.html")


@app.route("/public_access")
def public_access():
    return render_template("public_access.html")


@app.route("/about")
def about():
    return render_template("about.html")


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
