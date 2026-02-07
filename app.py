from flask import Flask, render_template, request, redirect
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for


def init_masters_table():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS masters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        service TEXT
    )
    """)

    conn.commit()
    conn.close()

app = Flask(__name__)

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "12345"

app.secret_key = "super_secret_key_123"  # можно любую строку

def add_master_column_to_orders():
    db = get_db()
    try:
        db.execute("ALTER TABLE orders ADD COLUMN master_id INTEGER")
        db.commit()
        print("Колонка master_id добавлена в orders")
    except Exception as e:
        print("Колонка master_id уже существует или не может быть добавлена")


def get_db():
    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/service/<name>")
def service(name):
    return render_template("service.html", name=name)

@app.route("/order", methods=["POST"])
def order():
    name = request.form["name"]
    phone = request.form["phone"]
    service = request.form["service"]
    address = request.form.get("address", "")
    comment = request.form.get("comment", "")

    db = get_db()
    db.execute("""
        INSERT INTO orders (name, phone, service, address, comment, status)
        VALUES (?, ?, ?, ?, ?, 'Новый')
    """, (name, phone, service, address, comment))
    db.commit()

    return ("", 200)

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    status = request.args.get("status")
    db = get_db()

    if status:
        orders = db.execute("SELECT * FROM orders WHERE status = ?", (status,)).fetchall()
    else:
        orders = db.execute("SELECT * FROM orders").fetchall()

    masters = db.execute("SELECT * FROM masters").fetchall()

    return render_template("admin.html", orders=orders, masters=masters)

@app.route("/assign_master", methods=["POST"])
def assign_master():
    order_id = request.form["order_id"]
    master_id = request.form["master_id"]

    db = get_db()
    db.execute("UPDATE orders SET master_id = ?, status = 'В обработке' WHERE id = ?", (master_id, order_id))
    db.commit()

    return redirect("/admin?status=В обработке")

@app.route("/orders_count")
def orders_count():
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    return str(count)

@app.route("/update_status/<int:order_id>/<status>")
def update_status(order_id, status):
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()

    return redirect(f"/admin?status={status}")

@app.route("/admin/masters")
def admin_masters():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    db = get_db()
    masters = db.execute("SELECT * FROM masters").fetchall()
    return render_template("masters.html", masters=masters)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin/masters/add", methods=["POST"])
def add_master():
    name = request.form["name"]
    phone = request.form["phone"]
    service = request.form["service"]

    db = get_db()
    db.execute(
        "INSERT INTO masters (name, phone, service) VALUES (?, ?, ?)",
        (name, phone, service)
    )
    db.commit()
    db.close()

    return redirect("/admin/masters")


@app.route("/admin/masters/delete/<int:master_id>")
def delete_master(master_id):
    db = get_db()
    db.execute("DELETE FROM masters WHERE id = ?", (master_id,))
    db.commit()
    db.close()

    return redirect("/admin/masters")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        login = request.form["login"]
        password = request.form["password"]

        if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            error = "Неверный логин или пароль"

    return render_template("login.html", error=error)


if __name__ == "__main__":
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        service TEXT,
        address TEXT,
        comment TEXT,
        status TEXT DEFAULT 'Новый'
    )""")
    db.commit()
    init_masters_table()
    add_master_column_to_orders() 
    app.run(debug=True)

