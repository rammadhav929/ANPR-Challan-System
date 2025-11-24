from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    session,
    make_response,
    url_for,
)
import os
from predict import plate
from pymongo import MongoClient
import datetime
from flask_mail import Mail, Message
import threading

app = Flask(__name__)
mail = Mail(app)
app.secret_key = "your_secret_key"
client = MongoClient("mongodb://localhost:27017/")
db = client["license_plate"]
# print(db)
collection = db["vehicle"]
# print(collection)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "Keep Your own gmail Username"
app.config["MAIL_PASSWORD"] = "Don't keep your gmail password you generate it for flask mail follow you tube"
app.config["MAIL_USE_TLS"] = True
mail.init_app(app)
BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH, "static/upload/")
# database = {"ram": "123"}


def send_reminder_email(challan_id):
    with app.app_context():
        challan = db["challan"].find_one({"_id": challan_id})
        if challan:
            Ic_number = challan["Ic_number"]
            owner_name = challan["ownername"]
            email = challan["email"]
            violation = challan["offence"]
            datetime_of_offence = challan["datatime_of_offence"]
            print("Sending reminder email to:", email)
            msg = Message(
                "Reminder:Challan on your vehicle no:" + Ic_number,
                sender="b.rammadhav@gmail.com",
                recipients=[email],
            )
            msg.body = (
                "This is a reminder for the challan issued on your vehicle no:"
                + Ic_number
                + "due to"
                + violation
                + "on the owner of the vechicle"
                + owner_name
                + "on"
                + str(datetime_of_offence)
                + ".Please pay your challan as soon as possible."
            )
            try:
                mail.send(msg)
                print("Reminder email sent successfully!")
            except Exception as e:
                print("Failed to send reminder email:", str(e))


def schedule_reminder_email(challan_id):
    delay = 120
    timer = threading.Timer(delay, send_reminder_email, args=[challan_id])
    timer.start()


@app.route("/")
def hello_world():

    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    try:
        upload_file = request.files.get("image_name")
        if not upload_file:
            return render_template(
                "index.html", error="No file uploaded!", upload=False
            )

        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH, filename)
        upload_file.save(path_save)

        detected_plate = plate(path_save, filename)

        details = collection.find_one({"number_plate": detected_plate})

        return render_template(
            "index.html",
            upload=True,
            upload_image=filename,
            number_plate=detected_plate,  # ✔ send detected plate directly
            is_registered=bool(details),
            owner=details,
        )

    except Exception as e:
        return render_template(
            "index.html",
            error=str(e),
            upload=False,
            number_plate="",
            is_registered=False,
        )


@app.route("/create_challan", methods=["POST"])
def create_challan():
    try:
        # 1️⃣ Extract form fields safely
        plate_no = request.form.get("selected_plate")
        violation = request.form.get("violation")

        if not plate_no or not violation:
            return jsonify({"error": "Missing number_plate or violation"}), 400

        # 2️⃣ Fetch owner details
        try:
            details = collection.find_one({"number_plate": plate_no})
        except Exception as db_err:
            return jsonify({"error": "Database error", "details": str(db_err)}), 500

        if not details:
            return jsonify({"error": "Vehicle not registered"}), 400

        owner_name = details["name"]
        email = details["email"]
        current_time = datetime.datetime.now()

        # 3️⃣ Create challan entry
        challan = {
            "Ic_number": plate_no,
            "ownername": owner_name,
            "email": email,
            "offence": violation,
            "datetime_of_offence": current_time,
        }

        try:
            challan_id = db["challan"].insert_one(challan).inserted_id
        except Exception as insert_err:
            return (
                jsonify(
                    {"error": "Failed to create challan", "details": str(insert_err)}
                ),
                500,
            )

        # 4️⃣ Send email notification
        try:
            msg = Message(
                f"Challan for vehicle: {plate_no}",
                sender="b.rammadhav@gmail.com",
                recipients=[email],
            )
            msg.body = (
                f"Challan issued for vehicle {plate_no} due to {violation} "
                f"on {current_time}."
            )
            mail.send(msg)
        except Exception as mail_err:
            return (
                jsonify(
                    {
                        "error": "Challan created but email failed",
                        "details": str(mail_err),
                    }
                ),
                500,
            )

        # 5️⃣ Schedule reminder
        try:
            schedule_reminder_email(challan_id)
        except Exception as schedule_err:
            print("Scheduler error:", schedule_err)

        return redirect("/challans_page")

    except Exception as e:
        # Final safety net
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500


@app.route("/challans_page", methods=["GET", "POST"])
def challans_page():
    if request.method == "GET":
        challans = list(db["challan"].find())
        return render_template("nextpage.html", challans=challans)
    elif request.method == "POST":
        return redirect(url_for("index"))
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        plate = request.args.get("plate", "")
        print("see the plate number is    " + str(plate))
        return render_template("register.html", plate=plate)

    name = request.form["name"]
    email = request.form["email"]
    number_plate = request.form["number_plate"]

    # Insert to MongoDB
    collection.insert_one({"name": name, "email": email, "number_plate": number_plate})

    return "Registration Successful!"


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=3000)
