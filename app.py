from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
import os
from dotenv import load_dotenv

from firebase_config import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 10 tables in the restaurant
TABLE_NUMBERS = list(range(1, 11))


@app.route("/", methods=["GET", "POST"])
def user_booking():
    """
    User page to make a booking.
    Stores booking in Firestore collection 'bookings'.
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()
        persons = request.form.get("persons", "").strip()
        table_no = int(request.form.get("table_no"))

        if not (name and phone and date and time and persons):
            flash("Please fill all fields.", "error")
            return redirect(url_for("user_booking"))

        # Check if this table is already booked for this date & time
        bookings_ref = db.collection("bookings")
        conflict_query = (
            bookings_ref
            .where("table_no", "==", table_no)
            .where("date", "==", date)
            .where("time", "==", time)
            .where("status", "==", "booked")
        )
        conflict_docs = list(conflict_query.stream())

        if conflict_docs:
            flash(f"Table {table_no} is already booked for {date} at {time}. Please choose another table/time.", "error")
            return redirect(url_for("user_booking"))

        # Create booking
        booking_data = {
            "name": name,
            "phone": phone,
            "date": date,
            "time": time,
            "persons": int(persons),
            "table_no": table_no,
            "status": "booked"  # booked | completed | cancelled
        }

        new_doc = bookings_ref.add(booking_data)
        booking_id = new_doc[1].id

        flash(f"Booking confirmed! Your booking ID: {booking_id}", "success")
        return redirect(url_for("user_booking"))

    return render_template("user_booking.html", tables=TABLE_NUMBERS)


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """
    Simple admin login with password stored in .env (ADMIN_PASSWORD).
    """
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin password.", "error")

    return render_template("admin_login.html")


def admin_required(func):
    """
    Small helper decorator to check admin session.
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)

    return wrapper


# ---------------- ADMIN DASHBOARD ---------------- #

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """
    Show all bookings and allow admin to control slots.
    """
    bookings_ref = db.collection("bookings")
    # Order by date & time if you want
    bookings = []
    for doc in bookings_ref.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        bookings.append(data)

    # Sort in Python by date + time for nicer view
    bookings.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))

    return render_template("admin_dashboard.html", bookings=bookings)


@app.post("/admin/booking/<booking_id>/status")
@admin_required
def update_booking_status(booking_id):
    """
    Change booking status: booked / completed / cancelled.
    """
    new_status = request.form.get("status", "booked")
    db.collection("bookings").document(booking_id).update({"status": new_status})
    flash("Booking status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/booking/<booking_id>/delete")
@admin_required
def delete_booking(booking_id):
    """
    Delete a booking (freeing the slot).
    """
    db.collection("bookings").document(booking_id).delete()
    flash("Booking deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out.", "success")
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    # For local development
    app.run(debug=True)
