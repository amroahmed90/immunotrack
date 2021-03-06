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


@app.route("/health_worker_registration", methods=["POST", "GET"])
def health_worker_registration():
    # if the form get submitted and no users are logged in
    if (request.method == "POST") and ("user_id" not in session):
        # getting the inputs from the registration form and checking these inputs
        fname = request.form.get("fname")
        if not fname:
            return apology("First name was not provided", "/health_worker_registration")
        mname = request.form.get("mname")
        lname = request.form.get("lname")
        if not lname:
            return apology("Last name was not provided", "/health_worker_registration")
        social_number = request.form.get("social_number")
        if not social_number:
            return apology("Social number was not provided", "/health_worker_registration")
        # checking if this user has registered before using their unique social_number
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE social_number = ?", (social_number,))
            not_registered = len(c.fetchall())
            if not_registered:
                return apology("This social number has been registered before.", "/health_worker_registration")
        hospital = request.form.get("hospital")
        if not hospital:
            return apology("Place of work (hospital name) was not provided", "/health_worker_registration")
        email = request.form.get("email")
        if not email:
            return apology("Email was not provided", "/health_worker_registration")
        # checking if this user has registered before using their unique email
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE email = ?", (email,))
            not_registered = len(c.fetchall())
            if not_registered:
                return apology("This email has been registered before.", "/health_worker_registration")
        password = request.form.get("password")
        if not password:
            return apology("Password was not provided", "/health_worker_registration")
        password_confirmation = request.form.get("password_confirmation")
        if not password_confirmation:
            return apology("Password confirmation name was not provided", "/health_worker_registration")
        # checking if the password input does not match confirmation
        if password != password_confirmation:
            return apology("Password does not match the confirmation", "/health_worker_registration")
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
        # remember which user has logged in
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id FROM health_workers WHERE social_number = ?", (social_number,))
            user_id = c.fetchall()
            session["user_id"] = user_id[0][0]
            print(f"1 {session['user_id']}")
        return redirect("/health_worker_profile")
    # if there is a user logged in
    elif "user_id" in session:
        return redirect("/health_worker_profile")
    # if the method was GET
    else:
        return render_template("health_workers.html")


@app.route("/health_worker_login", methods=["GET", "POST"])
def health_worker_login():
    # if the form get submitted and no users are logged in
    if (request.method == "POST") and ("user_id" not in session):
        # getting the inputs from the registration form and checking these inputs
        email = request.form.get("email")
        if not email:
            return apology("Email was not provided.", "/health_worker_registration")
        password = request.form.get("password")
        if not password:
            return apology("Password was not provided.", "/health_worker_registration")
        # checking if health worker is in the database
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE email = ?", (email,))
            registered = len(c.fetchall())
            if not registered:
                return apology("This email has not been registered.", "/health_worker_registration")
        # checking if the password provided is the same as in the database when hashed
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id, password_hash FROM health_workers WHERE email = ?", (email,))
            result = c.fetchall()
            if check_password_hash(result[0][1], password):
                session["user_id"] = result[0][0]
                return redirect("/health_worker_profile")
            else:
                return apology("The password you provided is not correct.", "/health_worker_registration")
    # if the method was GET
    else:
        return render_template("health_workers.html")


@app.route("/health_worker_profile")
# @login_required
def health_worker_profile():
    # get the logged in health worker
    with sqlite3.connect("immunotrack.db") as conn:
        # seting up a cursor on which you'll execute sqlite commands
        c = conn.cursor()
        c.execute(
            '''SELECT health_workers.first_name,
                health_workers.middle_name,
                health_workers.last_name,
                hospitals.hospital_name,
                health_workers.email
                FROM health_workers
                JOIN hospitals
                ON health_workers.work_hospital_id=hospitals.id
                WHERE health_workers.id = ?;''', (session["user_id"],))
        user_data = c.fetchall()
        return render_template("health_worker_profile.html", user_data=user_data[0])


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
