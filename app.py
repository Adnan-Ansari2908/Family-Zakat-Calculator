from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_USERNAME = "cy"
ADMIN_PASSWORD = "admincy901"

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS families (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        family_name TEXT,
        gold_grams REAL,
        gold_purity TEXT,
        silver_grams REAL,
        cash REAL,
        property REAL,
        business REAL,
        debts REAL,
        total REAL,
        zakat REAL,
        eligible TEXT,
        date TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY,
        gold_24k REAL,
        silver REAL
    )
    """)

    c.execute("INSERT OR IGNORE INTO prices (id, gold_24k, silver) VALUES (1, 16102, 285)")
    conn.commit()
    conn.close()

init_db()

def get_prices():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT gold_24k, silver FROM prices WHERE id=1")
    data = c.fetchone()
    conn.close()
    return data

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/form", methods=["POST"])
def form():
    family_name = request.form["family_name"]
    return render_template("form.html", family_name=family_name)

@app.route("/submit", methods=["POST"])
def submit():
    family_name = request.form["family_name"]
    gold = float(request.form["gold"])
    purity = request.form["purity"]
    silver = float(request.form["silver"])
    cash = float(request.form["cash"])
    property_val = float(request.form["property"])
    business = float(request.form["business"])
    debts = float(request.form["debts"])

    gold_24k_price, silver_price = get_prices()

    if purity == "22K":
        gold_price = gold_24k_price * (22/24)
    elif purity == "18K":
        gold_price = gold_24k_price * (18/24)
    else:
        gold_price = gold_24k_price

    gold_value = gold * gold_price
    silver_value = silver * silver_price

    total_assets = gold_value + silver_value + cash + property_val + business
    net_wealth = total_assets - debts

    nisab = 612.36 * silver_price

    eligible = "Yes" if net_wealth >= nisab else "No"
    zakat = net_wealth * 0.025 if eligible == "Yes" else 0

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO families 
        (family_name, gold_grams, gold_purity, silver_grams, cash, property, business, debts, total, zakat, eligible, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (family_name, gold, purity, silver, cash, property_val, business, debts, net_wealth, zakat, eligible, datetime.now()))
    conn.commit()
    conn.close()

    return render_template("result.html",
                           family_name=family_name,
                           total=net_wealth,
                           zakat=zakat,
                           eligible=eligible)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("admin_login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM families ORDER BY date DESC")
    families = c.fetchall()
    prices = get_prices()
    conn.close()

    return render_template("admin_dashboard.html", families=families, prices=prices)

@app.route("/update_prices", methods=["POST"])
def update_prices():
    if "admin" not in session:
        return redirect("/admin")

    gold = float(request.form["gold"])
    silver = float(request.form["silver"])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE prices SET gold_24k=?, silver=? WHERE id=1", (gold, silver))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
