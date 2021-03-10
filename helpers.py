from functools import wraps
from flask import session, redirect, render_template


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return apology("You have to be logged in to access this page.", "/health_worker_login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, link):
    return render_template("apology.html", message=message, link=link)
