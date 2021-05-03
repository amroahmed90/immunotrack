from functools import wraps
from flask import session, render_template
import csv
import urllib.request
import time


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    time.sleep(2)

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return apology("You have to be logged in to access this page.", "/health_worker_login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, link):
    return render_template("apology.html", message=message, link=link)


# defining a function that gets a list of all the countries whose vaccination data are available
def get_country_list():
    # getting the list of countries in the online database
    url_locations = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/locations.csv"
    # storing the list of countries
    locations_page = urllib.request.urlopen(url_locations)
    locations_page_lines = [l.decode('utf-8')
                            for l in locations_page.readlines()]
    locations_reader = csv.reader(locations_page_lines)
    country_list = []
    next(locations_reader)
    for location in locations_reader:
        country_list.append(location[0])
    return country_list

# function that returns true if new number is more than or equal to the old one, otherwise false


def check_number(new_number, old_number):
    # sometimes, the input field is an empty string
    if not new_number:
        new_number = 0
    # convert the string to number
    new_number = int(float(new_number))
    old_number = int(float(old_number))
    if new_number > old_number:
        return True
    else:
        return False


# defining a function that retrieves the vaccination data
def get_country_data(country):
    url_country_data = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/country_data/" + \
        country.replace(" ", "%20") + ".csv"
    country_page = urllib.request.urlopen(url_country_data)
    country_page_lines = [l.decode('utf-8') for l in country_page.readlines()]
    country_reader = csv.reader(country_page_lines)
    country_dict = {}
    country_dict["country"] = country
    country_dict["total_vaccinations"] = 0
    country_dict["people_vaccinated"] = 0
    country_dict["people_fully_vaccinated"] = 0
    next(country_reader)
    for data in country_reader:
        country_dict["last_updated"] = data[1]
        country_dict["vaccines"] = data[2]
        country_dict["source"] = data[3]
        if check_number(data[4], country_dict["total_vaccinations"]):
            country_dict["total_vaccinations"] = data[4]
        if check_number(data[5], country_dict["people_vaccinated"]):
            country_dict["people_vaccinated"] = data[5]
        if check_number(data[6], country_dict["people_fully_vaccinated"]):
            country_dict["people_fully_vaccinated"] = data[6]
    return country_dict


def format_number(value):
    return format(int(value), ',d')
