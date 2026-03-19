from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from .db import get_connection

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.config["SECRET_KEY"] = "super_secret_key_123"



@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        password_hash = generate_password_hash(data["password"])

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO employees
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            data["employee_id"],
            data["employee_name"],
            data["phone"],
            data["email"],
            data["domain"],
            data["username"],
            password_hash
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM employees WHERE username=%s", (username,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session["employee_id"] = user["employee_id"]

            cursor.execute("""
                INSERT INTO attendance (employee_id, in_time)
                VALUES (%s, %s)
            """, (user["employee_id"], datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()

            return redirect("/dashboard")

        return "Invalid username or password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "employee_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    employee_id = session.get("employee_id")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE attendance
        SET out_time = NOW()
        WHERE employee_id = %s AND out_time IS NULL
    """, (employee_id,))

    conn.commit()
    cursor.close()
    conn.close()

    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
