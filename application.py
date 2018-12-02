import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST(as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("missing symbol", 400)

        # Ensure shares was submitted
        if not shares:
            return apology("missing shares", 400)

        # Cast shares to integer
        shares = int(shares)

        # Ensure shares was valid
        if shares < 0:
            return apology("invalid shares")

        # Retrieve stock quote
        quote = lookup(request.form.get("symbol"))

        # Ensure stock quote is valid
        if not quote:
            return apology("invalid symbol", 400)

        # Select cash from users table
        cash = db.execute("SELECT cash from users WHERE id = :users_id", users_id = session['user_id'])

        cash = cash[0]['cash']

        # total price of shares
        price_of_shares = quote['price'] * shares

        # Ensure user afford the stock
        if price_of_shares > cash:
            return apology("can't afford", 400)

        # Select user shares of symbol
        user_shares = db.execute("SELECT shares FROM portfolios \
                WHERE users_id = :users_id AND symbol = :symbol",
                                users_id=session["user_id"],
                                symbol=quote["symbol"])

        # If user doesn't already have that stock --> create a new object
        if not user_shares:
            db.execute("INSERT INTO portfolios (shares, symbol, users_id) \
                        VALUES(:shares, :symbol, :users_id)",
                    shares=shares,
                    symbol=quote["symbol"],
                    users_id=session["user_id"])

        # buying the same stock
        # If user already has it --> increase number of shares
        else:
            shares_total = int(user_shares[0]["shares"]) + shares
            db.execute("UPDATE portfolios SET shares=:shares \
                        WHERE users_id=:users_id AND symbol=:symbol",
                    shares=shares_total,
                    users_id=session["user_id"],
                    symbol=quote["symbol"])

        # update cash
        db.execute("UPDATE users SET cash = cash - :price_of_shares WHERE id = :users_id", price_of_shares = price_of_shares, users_id = session['user_id'])

        # Redirect user to home page
        return redirect('/')

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Retrieve stock quote
        quote = lookup(request.form.get("symbol"))

        # Ensure stock quote is valid
        if not quote:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])

    # User reached route via GET (as by clicking a link)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST(as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 403)

        # Check password match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Hash the password
        hash_password = generate_password_hash(request.form.get("password"), )

        # Insert username and hash in database
        new_user_id = db.execute("INSERT INTO users(username, hash) VALUES(:username, :hash)",
                    username=request.form.get("username"), hash=hash_password)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exist
        if not new_user_id:
            return apology("usename already exists")

        # Remember which user has logged in
        # session["user_id"] = rows[0]["id"]
        session["user_id"] = new_user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
