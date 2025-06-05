import random

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlite3 import IntegrityError

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///final_project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Allows users to register for an account


@app.route("/register", methods=["GET", "POST"])
def register():
    print("Register route accessed")
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensures a name was submitted
        if not name:
            return render_template("apology.html", error_message="Missing name")

        # Ensure username was submitted
        if not username:
            return render_template("apology.html", error_message="Missing username")

        # Ensure password was submitted
        if not password:
            return render_template("apology.html", error_message="Missing password")

        # Ensure confirmation was submitted
        if not confirmation or confirmation != password:
            return render_template("apology.html", error_message="Passwords don't match")

        # Check if the username already exists and insert new username and hashed password into the table
        try:
            id = db.execute("INSERT INTO users (first_name, username, password) VALUES(?, ?, ?)", name,
                            username, generate_password_hash(password))
            print(id)
        except IntegrityError:
            return render_template("apology.html", error_message="Username taken")

        return redirect("/")

    else:
        return render_template("register.html")

# Logs user into the site


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("apology.html", error_message="Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("apology.html", error_message="Must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return render_template("apology.html", error_message="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Logs user out of the site


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Allows user to change their password


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":

        # Get values
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        username = db.execute("SELECT username FROM users WHERE id = ?",
                              session.get("user_id"))[0]["username"]

        # Ensure password was submitted
        if not password:
            return render_template("apology.html", error_message="Missing password")

        # Ensure confirmation was submitted
        if not confirmation or confirmation != password:
            return render_template("apology.html", error_message="Passwords don't match")

        # Updates the password in the database
        db.execute("UPDATE users SET password = ? WHERE username = ?",
                   generate_password_hash(password), username)

        return redirect("/")

    else:
        return render_template("change_password.html")

# Homepage displaying welcome message


@app.route("/")
@login_required
def index():
    user_id = session.get("user_id")

    name = db.execute("SELECT first_name FROM users WHERE id = ?", user_id)
    if name:
        name = name[0]["first_name"]

    return render_template("index.html", name=name)

# Allows users to type and submit journal entries


@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    if request.method == "POST":

        user_id = session.get("user_id")
        entry = request.form.get("entry")

        # Checks if the entry is empty
        if not entry:
            return render_template("apology.html", error_message="Empty journal entry. Please type something in.")

        # Inserts the entry into the database and changes the date to be the user's local time
        db.execute(
            "INSERT INTO journal (user_id, entry, date) VALUES (?, ?, datetime('now', 'localtime'))", user_id, entry)

        return redirect("/entries")

    else:
        return render_template("journal.html")

# Page where users can view their journal entries


@app.route("/entries")
@login_required
def entries():
    user_id = session.get("user_id")

    # Gets the entry and date from the journal database to display in a table
    entry_date = db.execute(
        "SELECT entry, date FROM journal WHERE user_id = ? ORDER BY date DESC", user_id)

    return render_template("entries.html", entry_date=entry_date)

# Allows users to track the amount of sleep they get


@app.route("/sleep", methods=["GET", "POST"])
@login_required
def sleep():
    if request.method == "POST":
        user_id = session.get("user_id")
        sleep = request.form.get("sleep")

        # Checks if sleep is a whole number
        if not sleep.isnumeric():
            return render_template("apology.html", error_message="Please enter the hours of sleep you got to the nearest hour")

        sleep = int(sleep)

        # Makes sure hours are within reasonable bounds
        if sleep < 0 or sleep > 24:
            return render_template("apology.html", error_message="Please enter a number between 0 and 24.")

        # Inserts user's information into sleep database
        db.execute(
            "INSERT INTO sleep (user_id, hours_sleep, date) VALUES (?, ?, datetime('now', 'localtime'))", user_id, sleep)

        # Takes user to habits page so they can see their results
        return redirect("/habits")

    else:
        return render_template("sleep.html")

# Allows users to record the amount of screentime they had


@app.route("/screentime", methods=["GET", "POST"])
@login_required
def screentime():
    if request.method == "POST":

        user_id = session.get("user_id")

        hours_screen = request.form.get("hours_screen")
        minutes_screen = request.form.get("minutes_screen")

        if not hours_screen.isnumeric():
            return render_template("apology.html", error_message="Please enter a value between 0 and 24")

        hours_screen = int(hours_screen)

        if not minutes_screen.isnumeric():
            return render_template("apology.html", error_message="Please enter a value between 0 and 59")

        minutes_screen = int(minutes_screen)

        # Guarantees this combination can't exist because it doesn't make sense logically (exceeds time in a day)
        if hours_screen == 24 and minutes_screen > 0:
            return render_template("apology.html", error_message="Please enter values approrpriate for a 24 hour period.")

        if hours_screen < 0 or hours_screen > 24 or minutes_screen < 0 or minutes_screen > 59:
            return render_template("apology.html", error_message="Please enter approrpriate values. Hours should be between 0 and 24. Minutes should be between 0 and 59.")

        db.execute("INSERT INTO screentime (user_id, hours_screen, minutes_screen, date) VALUES (?, ?, ?, datetime('now', 'localtime'))",
                   user_id, hours_screen, minutes_screen)

        return redirect("/habits")

    else:
        return render_template("screentime.html")

# Allows users to track the amount of exercise that they've done


@app.route("/exercise", methods=["GET", "POST"])
@login_required
def exercise():
    if request.method == "POST":

        user_id = session.get("user_id")

        hours_exercise = request.form.get("hours_exercise")
        minutes_exercise = request.form.get("minutes_exercise")

        if not hours_exercise.isnumeric():
            return render_template("apology.html", error_message="Please enter a value between 0 and 24")

        hours_exercise = int(hours_exercise)

        if not minutes_exercise.isnumeric():
            return render_template("apology.html", error_message="Please enter a value between 0 and 59")

        minutes_exercise = int(minutes_exercise)

        if hours_exercise == 24 and minutes_exercise > 0:
            return render_template("apology.html", error_message="Please enter values approrpriate for a 24 hour period.")

        if hours_exercise < 0 or hours_exercise > 24 or minutes_exercise < 0 or minutes_exercise > 59:
            return render_template("apology.html", error_message="Please enter approrpriate values. Hours should be between 0 and 24. Minutes should be between 0 and 59.")

        db.execute("INSERT INTO exercise (user_id, hours_exercise, minutes_exercise, date) VALUES (?, ?, ?, datetime('now', 'localtime'))",
                   user_id, hours_exercise, minutes_exercise)

        return redirect("/habits")

    else:
        return render_template("exercise.html")

# Allows users to view their logged values in a table


@app.route("/habits")
@login_required
def habits():
    user_id = session.get("user_id")

    name = db.execute("SELECT first_name FROM users WHERE id = ?", user_id)
    if name:
        name = name[0]["first_name"]

    # Calculates the average sleep to display
    s_avg = db.execute("SELECT AVG(hours_sleep) FROM sleep WHERE user_id = ?", user_id)
    if s_avg:
        s_avg = s_avg[0]["AVG(hours_sleep)"]

    # Retrieves hours of sleep and date recorded to display
    sleep_date = db.execute(
        "SELECT hours_sleep, date FROM sleep WHERE user_id = ? ORDER BY date DESC", user_id)

    # Converts the hours of exercise recorded to minutes and averages that value
    e_avg = db.execute(
        "SELECT AVG((hours_exercise * 60) + minutes_exercise) as e_avg FROM exercise WHERE user_id = ?", user_id)
    if e_avg:
        e_avg = e_avg[0]["e_avg"]

    # Retrieves the hours, minutes, and date to display
    exercise_date = db.execute(
        "SELECT hours_exercise, minutes_exercise, date FROM exercise WHERE user_id = ? ORDER BY date DESC", user_id)

    # Does the same thing but with the values in the screentime database
    sc_avg = db.execute(
        "SELECT AVG((hours_screen * 60) + minutes_screen) as sc_avg FROM screentime WHERE user_id = ?", user_id)
    if sc_avg:
        sc_avg = sc_avg[0]["sc_avg"]

    screen_date = db.execute(
        "SELECT hours_screen, minutes_screen, date FROM screentime WHERE user_id = ? ORDER BY date DESC", user_id)

    return render_template("habits.html", name=name, s_avg=s_avg, sleep_date=sleep_date, e_avg=e_avg, exercise_date=exercise_date, sc_avg=sc_avg, screen_date=screen_date)

# Displays random affirmations


@app.route("/affirmations")
@login_required
def affirmations():
    # Generates a random integer, which populates a random affirmation upon refreshing page
    rand_int = random.randint(1, 5)
    return render_template("affirmations.html", rand_int=rand_int)
