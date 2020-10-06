import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
    stocks = db.execute("SELECT symbol, SUM(share) as total_shares FROM transact WHERE id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
    
    quotes = {}

    for stock in stocks:
        quotes[stock["symbol"]] = lookup(stock["symbol"])

    cash_remaining = float(users[0]["cash"])
    total = cash_remaining

    return render_template("index.html", quotes=quotes, stocks=stocks, total=total, cash_remaining=cash_remaining)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))

        if not quote:
            return apology("Invalid Symbol",401)

        share = int(request.form.get("shares"))

        curr_cash = db.execute("Select * from users where (id = :user_id) ",user_id = session["user_id"])
        
        money = float(curr_cash[0]["cash"])
        price = float(quote["price"])

        print(price)
        print(share)
        print(money)

        if(price*share > money):
            return apology("Can't Afford 🤪")

        left_cash = money - price*share
        print(type(left_cash))

        db.execute("update users set cash = :left_money where id = :user_id",left_money = left_cash, user_id = session["user_id"])

        db.execute("INSERT INTO transact (id, symbol, share, price,transactionTime) VALUES(:user_id, :symbol, :shares, :price, :timeTrans)",user_id=session["user_id"],symbol=request.form.get("symbol"),shares=share,price=price,timeTrans = str(datetime.now()))

        flash("Bought!")

        return redirect('/')

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("select * from transact where id = :user_id",user_id = session["user_id"])
    return render_template("history.html",transactions = transactions)


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
    if request.method == "POST":
        quote = lookup(request.form.get("quote"))

        if not quote:
            return apology("Invalid Symbol",401)

        return render_template("quoted.html",quote = quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if(request.method == "POST"):
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirm"):
            return apology("must confirm password", 400)

        elif not request.form.get("password") == request.form.get("confirm"):
            return apology("passwords do not match", 400)

        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = :name",name=username)

        if len(rows) == 1:
            return apology("Username already taken", 400)

        new_user_info = db.execute("Insert into users (username,hash) values(:username,:hash)",username=username,hash= generate_password_hash(password))

        session['user_id'] = new_user_info

        flash('Registered')

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        share = int(request.form.get("shares"))
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("Missing Symbol",408)

        total_shares = db.execute("select sum(share) as share from transact where (id = :user_id) and (symbol = :symbol)",user_id =  session["user_id"], symbol = symbol)[0]['share']

        print(total_shares)

        # total_shares = int(total_shares["symbol"][0])

        if(total_shares < share):
            return apology("You Don't have enough",408)

        info = lookup(symbol)
        price = info["price"]

        curr_cash = db.execute("Select * from users where (id = :user_id) ",user_id = session["user_id"])
        
        money = float(curr_cash[0]["cash"])

        money = money + share*price

        db.execute("update users set cash = :money where id = :user_id",money = money, user_id = session["user_id"])

        db.execute("INSERT INTO transact (id, symbol, share, price,transactionTime) VALUES(:user_id, :symbol, :shares, :price, :timeTrans)",user_id=session["user_id"],symbol=symbol,shares= -1 * share , price=price,timeTrans = str(datetime.now()))

        flash("Sold!")

        return redirect("/")
    else:
        transact = db.execute("SELECT symbol, SUM(share) as total_shares FROM transact WHERE id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
        print(type(transact))

        print(transact)

        symbols = []
        for i in range(len(transact)):
            symbols.append(transact[i]["symbol"])
        return render_template("sell.html",symbols = symbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
