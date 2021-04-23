import sqlite3
from helpers import login_required, apology, get_country_list, get_country_data, format_number
from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import csv
import urllib.request


# setting up the flask application
app = Flask(__name__)

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
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
    # if the form get submitted and no users are logged in
    if (request.method == "POST") and ("user_id" not in session):
        # getting the inputs from the registration form and checking these inputs
        fname = request.form.get("fname").title()
        if not fname:
            return apology("First name was not provided", "/health_worker_registration")
        mname = request.form.get("mname").title()
        lname = request.form.get("lname").title()
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
        email = request.form.get("email").lower()
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
        email = request.form.get("email").lower()
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
@login_required
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


# a route to handle adding new public (patient\vaccine taker) record
@app.route("/add_public", methods=["POST", "GET"])
@login_required
def add_public():
    if request.method == "POST":
        # getting the inputs from the registration form and checking these inputs
        first_name = request.form.get("first_name").title()
        if not first_name:
            return apology("First name was not provided", "/health_worker_registration")
        middle_name = request.form.get("middle_name").title()
        last_name = request.form.get("last_name").title()
        if not last_name:
            return apology("Last name was not provided", "/health_worker_registration")
        social_number = request.form.get("social_number")
        if not social_number:
            return apology("Social number was not provided", "/health_worker_registration")
        # checking if this user has registered before using their unique social_number
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE social_number = ?", (social_number,))
            not_registered = len(c.fetchall())
            if not_registered:
                # note: direct to update info url when set up
                return apology("This social number has been registered before.", "/health_worker_registration")
        email = request.form.get("email").lower()
        if not email:
            return apology("Email was not provided.", "/health_worker_registration")
        # checking if this user has registered before using their unique email
        with sqlite3.connect("immunotrack.db") as conn:
            # seting up a cursor on which you'll execute sqlite commands
            c = conn.cursor()
            c.execute(
                "SELECT * FROM public WHERE email = ?", (email,))
            not_registered = len(c.fetchall())
            if not_registered:
                # note: direct to update info url when set up
                return apology("This email has been registered before.", "/health_worker_registration")
        pre_infected = 1 if request.form.get(
            "pre_infected") == "yes" else 0
        pre_infection_date = request.form.get("pre_infection_date")
        pre_reinfected = 1 if request.form.get(
            "pre_reinfected") == "yes" else 0
        pre_reinfection_date = request.form.get("pre_reinfection_date")
        vaccinated = 1 if request.form.get(
            "vaccinated") == "yes" else 0
        vaccine_name = request.form.get("vaccine_name")
        vaccine_id = None
        print(vaccine_name)
        if vaccine_name != None:
            # check if vaccine type is in db
            with sqlite3.connect("immunotrack.db") as conn:
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
        with sqlite3.connect("immunotrack.db") as conn:
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
            (first_name, middle_name, last_name,                                                                                                   social_number, email, pre_infected, pre_infection_date, pre_reinfected, pre_reinfection_date, vaccinated, vaccine_type, vaccination_hospital_id, vaccinating_person_id, vaccination_date_1, vaccination_date_2, post_infected, post_infection_date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (first_name, middle_name, last_name, social_number, email, pre_infected, pre_infection_date, pre_reinfected, pre_reinfection_date, vaccinated, vaccine_id, vaccination_hospital_id[0][0], vaccinating_person_id, vaccination_date_1, vaccination_date_2, post_infected, post_infection_date))
            conn.commit()
            return render_template("success.html")

    else:
        with sqlite3.connect("immunotrack.db") as conn:
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
            print(vaccines[0][0])
            return render_template("add_public.html", health_worker_data=health_worker_data[0], vaccines=vaccines)


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
