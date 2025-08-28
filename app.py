from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
import os

app = Flask(__name__)
CORS(app)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deliveries.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email config (set in Render dashboard as env vars)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASS')
mail = Mail(app)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subcontractor = db.Column(db.String(100))
    company = db.Column(db.String(100))
    delivery_type = db.Column(db.String(100))
    email = db.Column(db.String(100))
    notes = db.Column(db.Text)
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    status = db.Column(db.String(20), default="Pending")

def serialize_booking(b):
    return {
        "id": b.id,
        "subcontractor": b.subcontractor,
        "company": b.company,
        "deliveryType": b.delivery_type,
        "email": b.email,
        "notes": b.notes,
        "date": b.date,
        "time": b.time,
        "status": b.status
    }

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([serialize_booking(b) for b in bookings])

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.json
    booking = Booking(
        subcontractor=data["subcontractor"],
        company=data["company"],
        delivery_type=data["deliveryType"],
        email=data["email"],
        notes=data.get("notes", ""),
        date=data["date"],
        time=data["time"],
        status="Pending"
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking submitted"}), 201

@app.route("/api/bookings/<int:id>", methods=["PUT"])
def update_booking(id):
    booking = Booking.query.get(id)
    if not booking:
        return jsonify({"error": "Not found"}), 404
    data = request.json
    booking.status = data.get("status", booking.status)
    db.session.commit()

    # Send email notification
    try:
        msg = Message(
            subject=f"Delivery Booking {booking.status} - Harwin Project",
            sender=app.config['MAIL_USERNAME'],
            recipients=[booking.email]
        )
        msg.body = f"""
        Dear {booking.subcontractor},

        Your delivery booking for {booking.date} at {booking.time}
        ({booking.delivery_type}) has been {booking.status}.

        Regards,
        Knights Brown Construction
        """
        mail.send(msg)
    except Exception as e:
        print("Email error:", e)

    return jsonify({"message": "Booking updated and email sent"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
