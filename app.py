import sqlite3
from helpers import login_required, apology, get_country_list, get_country_data, format_number
from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions
import os

# setting up the flask application
app = Flask(__name__)
app.secret_key = os.urandom(12).hex()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# custom filter
app.jinja_env.filters["format_number"] = format_number
app.jinja_env.globals.update(format_number=format_number)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# globals
db_name = "immunotrack.db"


# default route
@app.route("/")
def index():
    country_list = get_country_list()
    return render_template("index.html", country_list=country_list)


@app.route("/country-search")
def country_search():
    country_list = get_country_list()
    try:
        country = request.args.get("country").title()
    except:
        return apology("Please make you sure you typed the country name correctly.", "/")
    if country not in country_list:
        return apology("Please make you sure you typed the country name correctly.", "/")
    # get the vaccination data on the requested country
    country_dict = get_country_data(country)
    print(country_dict)
    return render_template("country-search.html", country_list=country_list, country_dict=country_dict)


@app.route("/health_worker_registration", methods=["POST", "GET"])
def health_worker_registration():
    route_name = "/health_worker_registration"
    # if the form get submitted and no users are logged in
    if (request.method == "POST") and ("user_id" not in session.keys()):
        # getting the inputs from the registration form and checking these inputs
        fname = request.form.get("fname").title()
        if not fname:
            return apology("First name was not provided", route_name)
        mname = request.form.get("mname").title()
        lname = request.form.get("lname").title()
        if not lname:
            return apology("Last name was not provided", route_name)
        social_number = request.form.get("social_number")
        if not social_number:
            return apology("Social number was not provided", route_name)
        # checking if this user has registered before using their unique social_number
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE social_number = ?", (social_number,))
            not_registered = len(c.fetchall())
            if not_registered:
                return apology("This social number has been registered before.", route_name)
        hospital = request.form.get("hospital")
        if not hospital:
            return apology("Place of work (hospital name) was not provided", route_name)
        # add the hospital to the database if it's not there
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM hospitals WHERE hospital_name = ?", (hospital, ))
            hospital_result = c.fetchall()
            print(hospital_result)
            if not len(hospital_result):
                c.execute(
                    "INSERT INTO hospitals (hospital_name) VALUES (?)", (hospital, ))
                conn.commit()
        email = request.form.get("email").lower()
        if not email:
            return apology("Email was not provided", route_name)
        # checking if this user has registered before using their unique email
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE email = ?", (email,))
            not_registered = len(c.fetchall())
            if not_registered:
                return apology("This email has been registered before.", route_name)
        password = request.form.get("password")
        if not password:
            return apology("Password was not provided", route_name)
        password_confirmation = request.form.get("password_confirmation")
        if not password_confirmation:
            return apology("Password confirmation name was not provided", route_name)
        # checking if the password input does not match confirmation
        if password != password_confirmation:
            return apology("Password does not match the confirmation", route_name)
        # hashing the passord
        hashed = generate_password_hash(password)
        # sql queries
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id FROM hospitals WHERE hospital_name = ?", (hospital,))
            hospital_id = c.fetchall()
            c.execute("""INSERT INTO health_workers (first_name, middle_name, last_name, social_number, work_hospital_id, email, password_hash)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (fname, mname, lname, social_number, hospital_id[0][0], email, hashed))
            conn.commit()
        # remember which user has logged in
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id FROM health_workers WHERE social_number = ?", (social_number,))
            user_id = c.fetchall()
            session["user_id"] = user_id[0][0]
            session["type"] = "health_worker"
        return redirect("/health_worker_profile")
    # if there is a user already logged in as a health worker
    elif "type" in session.keys():
        if session["type"] == "health_worker":
            return redirect("/health_worker_profile")
        # if the method was GET but user is logged in as a public
        else:
            return apology("You can't access this page if you are logged in as public. Please log out and try again.", "/public_access_profile")
    # if the method was GET and they are not logged in
    else:
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT hospital_name FROM hospitals")
            hospitals_list = c.fetchall()
            return render_template("health_workers.html", hospitals_list=hospitals_list)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/health_worker_login", methods=["GET", "POST"])
def health_worker_login():
    route_name = "/health_worker_login"
    # if the form get submitted and no users are logged in as a health worker
    if (request.method == "POST") and ("user_id" not in session.keys()):
        # getting the inputs from the registration form and checking these inputs
        email = request.form.get("email").lower()
        if not email:
            return apology("Email was not provided.", route_name)
        password = request.form.get("password")
        if not password:
            return apology("Password was not provided.", route_name)
        # checking if health worker is in the database
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM health_workers WHERE email = ?", (email,))
            registered = len(c.fetchall())
            if not registered:
                return apology("This email has not been registered.", route_name)
        # checking if the password provided is the same as in the database when hashed
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT id, password_hash FROM health_workers WHERE email = ?", (email,))
            result = c.fetchall()
            if check_password_hash(result[0][1], password):
                session["user_id"] = result[0][0]
                session["type"] = "health_worker"
                return redirect("/health_worker_profile")
            else:
                return apology("The password you provided is not correct.", route_name)
    # if the method was GET and user signed in as public
    elif ("user_id" in session.keys()) and (session["type"] != "health_worker"):
        return apology("You can't access this page while logged in as a public member, please log out first", "/public_access_profile")
    # if te method is GET
    else:
        return render_template("health_workers.html")


@app.route("/health_worker_profile")
@login_required
def health_worker_profile():
    if session["type"] != "health_worker":
        return apology("You need to be logged in as a health worker to access this page. Please log out and try again.", "/public_access_profile")
    # get the logged in health worker
    with sqlite3.connect(db_name) as conn:
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


# a route to handle adding new public (patient\vaccine taker) record
@app.route("/add_public", methods=["POST", "GET"])
def add_public():
    route_name = "/health_worker_registration"
    if request.method == "POST":
        # getting the inputs from the registration form and checking these inputs
        first_name = request.form.get("first_name").title()
        if not first_name:
            return apology("First name was not provided", route_name)
        middle_name = request.form.get("middle_name").title()
        last_name = request.form.get("last_name").title()
        if not last_name:
            return apology("Last name was not provided", route_name)
        social_number = request.form.get("social_number")
        if not social_number:
            return apology("Social number was not provided", route_name)
        # checking if this user has registered before using their unique social_number
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE social_number = ?", (social_number,))
            not_registered = len(c.fetchall())
            if not_registered:
                # note: direct to update info url when set up
                return apology("This social number has been registered before.", route_name)
        email = request.form.get("email").lower()
        if not email:
            return apology("Email was not provided.", route_name)
        phone = request.form.get("full_phone")
        if not phone:
            return apology("Phone number was not provided", route_name)
        # checking if this user has registered before using their unique email
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE email = ?", (email,))
            not_registered = len(c.fetchall())
            if not_registered:
                # note: direct to update info url when set up
                return apology("This email has been registered before.", route_name)
        pre_infected = 1 if request.form.get("pre_infected") == "yes" else 0
        pre_infection_date = request.form.get("pre_infection_date")
        pre_reinfected = 1 if request.form.get(
            "pre_reinfected") == "yes" else 0
        pre_reinfection_date = request.form.get("pre_reinfection_date")
        vaccinated = 1 if request.form.get("vaccinated") == "yes" else 0
        vaccine_name = request.form.get("vaccine_name")
        vaccine_id = None
        print(vaccine_name)
        if vaccine_name != None:
            # check if vaccine type is in db
            with sqlite3.connect(db_name) as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM vaccines WHERE vaccine_name = ?",
                          (vaccine_name, ))
                vaccine_id = c.fetchall()
                conn.commit()
                if not len(vaccine_id):
                    return apology("The vaccine you chose is not in the list. Make sure you choose from the list provided or contact us if the vaccine is not in the list.", "/add_public")
                # get vaccine id
                vaccine_id = vaccine_id[0][0]
                print(vaccine_id)
        vaccinating_person_id = session["user_id"]
        vaccination_date_1 = request.form.get("first_vaccination_date")
        vaccination_date_2 = request.form.get("second_vaccination_date")
        post_infected = 1 if request.form.get(
            "post_infected") == "yes" else 0
        post_infection_date = request.form.get("post_infection_date")
        # insert record to public table in the db
        # store registered record in the variable record
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            # retrieving the vaccination hospital id
            c.execute('''SELECT hospitals.id 
            FROM hospitals 
            JOIN health_workers 
            ON health_workers.work_hospital_id = hospitals.id 
            WHERE health_workers.id = ?;''', (session["user_id"], ))
            vaccination_hospital_id = c.fetchall()
            conn.commit()
            c.execute('''INSERT INTO public 
            (first_name, middle_name, last_name, social_number, email, phone, pre_infected, pre_infection_date, pre_reinfected, pre_reinfection_date, vaccinated, vaccine_type, vaccination_hospital_id, vaccinating_person_id, vaccination_date_1, vaccination_date_2, post_infected, post_infection_date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (first_name, middle_name, last_name, social_number, email, phone, pre_infected, pre_infection_date, pre_reinfected, pre_reinfection_date, vaccinated, vaccine_id, vaccination_hospital_id[0][0], vaccinating_person_id, vaccination_date_1, vaccination_date_2, post_infected, post_infection_date))
            conn.commit()
            return render_template("success.html")

    # if the user is logged in as public, access to this route is disallowed
    elif (request.method == "GET") and session["type"] != "health_worker":
        return apology("You need to be logged in as a health worker to access this page. Please log out and try again.", "/public_access_profile")
    else:
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute(
                '''SELECT health_workers.first_name,
                health_workers.middle_name,
                health_workers.last_name,
                hospitals.hospital_name
                FROM health_workers
                JOIN hospitals
                ON health_workers.work_hospital_id=hospitals.id
                WHERE health_workers.id = ?;''', (session["user_id"],))
            health_worker_data = c.fetchall()
            conn.commit()
            c.execute("SELECT vaccine_name FROM vaccines ORDER BY vaccine_name")
            vaccines = c.fetchall()
            conn.commit()
            return render_template("add_public.html", health_worker_data=health_worker_data[0], vaccines=vaccines)


# public access login route
@app.route("/public_access")
def public_access():
    # if user is already logged in as public
    if "user_id" not in session.keys():
        return render_template("public_access.html")
    elif session["type"] == "public":
        return redirect("/public_access_profile")
    else:
        return apology("You can't access this page if you are logged in as a health worker. Please log out and try again.", "/health_worker_profile")


# public access profile route
@app.route("/public_access_profile", methods=["GET", "POST"])
def public_access_profile():
    route_name = "/public_access"
    # if the method is POST and the user is not signed in
    if (request.method == "POST") and ("user_id" not in session.keys()):
        social_number = request.form.get("id_number")
        if not social_number:
            return apology("Social number was not provided.", route_name)
        email = request.form.get("email")
        if not email:
            return apology("Email was not provided.", route_name)
        # checking if the public member's social number and email are in the database
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE social_number = ?", (social_number,))
            social_number_registered = c.fetchall()
            if not social_number_registered:
                return apology("This social number has not been registered yet or incorrect.", route_name)
            c.execute(
                "SELECT * FROM public WHERE email = ?", (email,))
            email_registered = c.fetchall()
            if not email_registered:
                return apology("This email has not been registered yet or incorrect.", route_name)
            if (email_registered[0][5] != social_number_registered[0][5]) and (email_registered[0][4] != social_number_registered[0][4]):
                return apology("The email and social number you entered do not match.", route_name)
            user_data = email_registered[0]
            session["user_id"] = user_data[0]
            session["type"] = "public"
            vaccination_data = {}
            if user_data[11] != 0:
                # getting the vaccine name
                c.execute("SELECT vaccine_name FROM vaccines WHERE id = ?",
                          (user_data[12], ))
                vaccination_data["vaccine_type"] = c.fetchone()[0]
                # getting the hospital name
                c.execute("SELECT hospital_name FROM hospitals WHERE id = ?",
                          (user_data[13], ))
                vaccination_data["hospital"] = c.fetchone()[0]
                # getting the vaccinating person's name name
                c.execute("SELECT * FROM health_workers WHERE id = ?",
                          (user_data[14], ))
                vaccinating_person = c.fetchall()[0]
                vaccination_data["vaccinating_person"] = vaccinating_person[1] + \
                    " " + vaccinating_person[3]
            return render_template("public_access_profile.html", user_data=user_data, vaccination_data=vaccination_data)
    # check if logged in as public (method GET)
    elif ("user_id" in session.keys()) and (session["type"] == "public"):
        with sqlite3.connect(db_name) as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE id = ?", (session["user_id"],))
            user_data = c.fetchall()[0]
            vaccination_data = {}
            if user_data[11] != 0:
                # getting the vaccine name
                c.execute("SELECT vaccine_name FROM vaccines WHERE id = ?",
                          (user_data[12], ))
                vaccination_data["vaccine_type"] = c.fetchone()
                if vaccination_data["vaccine_type"] is not None:
                    vaccination_data["vaccine_type"] = vaccination_data["vaccine_type"][0]
                else:
                    vaccination_data["vaccine_type"] = "Not registered by health personnel."
                # getting the hospital name
                c.execute("SELECT hospital_name FROM hospitals WHERE id = ?",
                          (user_data[13], ))
                vaccination_data["hospital"] = c.fetchone()[0]
                # getting the vaccinating person's name name
                c.execute("SELECT * FROM health_workers WHERE id = ?",
                          (user_data[14], ))
                vaccinating_person = c.fetchall()[0]
                vaccination_data["vaccinating_person"] = vaccinating_person[1] + \
                    " " + vaccinating_person[3]
            return render_template("public_access_profile.html", user_data=user_data, vaccination_data=vaccination_data)
    else:
        return apology("You need to sign in as public not a health worker to access this page", "/health_worker_registration")


@app.route("/about")
def about():
    return render_template("about.html")


# handling incorrect urls
def errorhandler(e):
    return apology(str(e.code) + " " + e.name, "/")


for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


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
