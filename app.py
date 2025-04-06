from flask import (
    Flask,
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
database = {"ram": "123"}


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

    return render_template("login.html")


@app.route("/form_login", methods=["POST", "GET"])
def login():
    name1 = request.form["username"]
    pwd = request.form["password"]
    if name1 not in database:
        return render_template("login.html", info="Invalid User")
    else:
        if database[name1] != pwd:
            return render_template("login.html", info="Invalid password")
        else:
            session["username"] = name1  # Store username in session
            return redirect("/index")


@app.route("/index", methods=["POST", "GET"])
def index():
    if "username" not in session:
        return redirect("/")  # Redirect to login page if not logged in

    if request.method == "POST":
        upload_file = request.files["image_name"]
        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH, filename)
        upload_file.save(path_save)
        a = plate(path_save, filename)
        Ic_number = a
        violation = request.form.get("violation")
        details = collection.find_one({"number_plate": Ic_number})
        print(details)
        print(collection)
        if details:
            owner_name = details["name"]
            email = details["email"]
            current_time = datetime.datetime.now()
            challan = {
                "Ic_number": Ic_number,
                "ownername": owner_name,
                "email": email,
                "offence": violation,
                "datetime_of_offence": current_time,
            }
            challan_id = db["challan"].insert_one(challan).inserted_id
            msg = Message(
                "Challan on your vehicle no:" + Ic_number,
                sender="b.rammadhav@gmail.com",
                recipients=[email],
            )
            msg.body = (
                "Challan has been raised on your vehicle no: "
                + Ic_number
                + " due to "
                + violation
                + " on the owner of the vehicle "
                + owner_name
                + " on "
                + str(current_time)
                + ". Pay your challan before the due date i.e "
                + str(current_time + datetime.timedelta(days=15))
            )
            mail.send(msg)
            schedule_reminder_email(challan_id)

        # Perform image processing or any other logic
        return render_template(
            "index.html",
            upload=True,
            upload_image=filename,
            no=a,
        )
    return render_template("index.html", upload=False)


@app.route("/challans_page", methods=["GET", "POST"])
def challans_page():
    if request.method == "GET":
        challans = list(db["challan"].find())
        return render_template("nextpage.html", challans=challans)
    elif request.method == "POST":
        return redirect(url_for("index"))
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()  # Clear the session data
    response = make_response(redirect("/"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=3000)
