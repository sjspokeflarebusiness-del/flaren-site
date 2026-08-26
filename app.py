from flask import Flask, render_template, request, redirect, url_for, flash
import random
import string
from datetime import datetime
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "flaren-secret-key-change-in-production"

# ===== CONFIGURE THESE =====
OWNER_EMAIL = "sjspokeflarebusiness@gmail.com"
OWNER_PHONE = "8838969397"

APPS_SCRIPT_WEBHOOK_URL = os.getenv(
    "APPS_SCRIPT_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbzu3DUX5GsVlGNz5ts01dkZ6Vq7B9Wozr4BcP2iSr7mbF5vbCac27niA9_w66P3S7fOOw/exec"
)

# Optional SMTP config (leave blank if not using direct SMTP email)
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
# ===========================

SERVICES = [
    "Poster designs",
    "Wallpapers",
    "Invitations",
    "Presentation designs",
    "School project designs",
    "Digital templates",
    "Simple websites",
    "Small educational programming projects",
    "Custom digital work",
]

# Sample works items (adjust titles/descriptions as you like)
SAMPLE_WORKS = [
    {
        "key": "logo",
        "title": "Logo Design",
        "desc": "Our own FLAREN logo and branding visuals.",
        "image": "logo.png",  # your logo
    },
    {
        "key": "personal_portfolio",
        "title": "Personal Image Portfolio",
        "desc": "Curated personal photography and portrait work.",
        "image": "portfolio-1.png",
    },
    {
        "key": "advertisement_posters",
        "title": "Advertisement Posters",
        "desc": "Promotional posters for events and brands.",
        "image": "portfolio-2.png",
    },
    {
        "key": "digital_images",
        "title": "Digital Images",
        "desc": "Digital art, social media graphics, and banners.",
        "image": "portfolio-3.png",
    },
    {
        "key": "card_designs",
        "title": "Card Designs",
        "desc": "Business cards, greeting cards, and invitation cards.",
        "image": "portfolio-4.png",
    },
    {
        "key": "awesome_posters",
        "title": "Awesome Posters",
        "desc": "Bold, creative poster designs for various themes.",
        "image": "portfolio-5.png",
    },
    {
        "key": "extra_work",
        "title": "Featured Works",
        "desc": "Selected highlights from recent projects.",
        "image": "portfolio-6.png",
    },
]

def generate_order_id():
    now = datetime.now()
    ymd = now.strftime("%Y%m%d")
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"FLR-{ymd}-{rand}"

def send_to_sheets(payload):
    try:
        resp = requests.post(APPS_SCRIPT_WEBHOOK_URL, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

def send_email(subject, to_name, to_email, body_html):
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASS:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(body_html, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

@app.route("/")
def home():
    # Main landing page is now Sample Works
    return render_template("sample_works.html", sample_works=SAMPLE_WORKS)

@app.route("/sample-works")
def sample_works():
    return render_template("sample_works.html", sample_works=SAMPLE_WORKS)

@app.route("/services")
def services():
    return render_template("services.html", services=SERVICES)

@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("contactName", "").strip()
        email = request.form.get("contactEmail", "").strip()
        message = request.form.get("contactMessage", "").strip()

        payload = {
            "type": "contact",
            "date": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "message": message,
        }
        send_to_sheets(payload)

        # Email to owner
        owner_subject = f"New contact enquiry from {name}"
        owner_body_html = f"""
        <html>
          <body>
            <h2>New Contact Enquiry</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Message:</strong></p>
            <p>{message.replace("\n", "<br>")}</p>
          </body>
        </html>
        """
        send_email(owner_subject, "FLAREN Owner", OWNER_EMAIL, owner_body_html)

        # Confirmation email to user
        user_subject = "We received your message – FLAREN"
        user_body_html = f"""
        <html>
          <body>
            <h2>Thank you for contacting FLAREN</h2>
            <p>Hi {name},</p>
            <p>We have received your message and will get back to you soon.</p>
            <p><strong>Your message:</strong></p>
            <p>{message.replace("\n", "<br>")}</p>
            <p>Please check your email for further details and our reply.</p>
            <p>— Team FLAREN</p>
          </body>
        </html>
        """
        send_email(user_subject, name, email, user_body_html)

        flash("Message sent successfully. Please check your email for further details.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html", owner_email=OWNER_EMAIL, owner_phone=OWNER_PHONE)

@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        data = request.form
        order_id = generate_order_id()
        order_data = {
            "type": "order",
            "order_id": order_id,
            "date": datetime.now().isoformat(),
            "customer_name": data.get("customerName", "").strip(),
            "email": data.get("email", "").strip(),
            "phone": data.get("phone", "").strip(),
            "service": data.get("service", ""),
            "description": data.get("description", "").strip(),
            "deadline": data.get("deadline", ""),
            "reference_file": data.get("referenceFile", ""),
            "additional_requirements": data.get("additionalRequirements", "").strip(),
            "status": "New",
        }

        send_to_sheets(order_data)

        # Email to owner
        owner_subject = f"New Order – {order_id}"
        owner_body_html = f"""
        <html>
          <body>
            <h2>New Order Received</h2>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Date:</strong> {order_data["date"]}</p>
            <p><strong>Customer:</strong> {order_data["customer_name"]}</p>
            <p><strong>Email:</strong> {order_data["email"]}</p>
            <p><strong>Phone:</strong> {order_data["phone"]}</p>
            <p><strong>Service:</strong> {order_data["service"]}</p>
            <p><strong>Description:</strong><br>{order_data["description"].replace("\n", "<br>")}</p>
            <p><strong>Deadline:</strong> {order_data["deadline"] or "Not specified"}</p>
            <p><strong>Additional Requirements:</strong><br>{order_data["additional_requirements"].replace("\n", "<br>") or "None"}</p>
            <p><strong>Status:</strong> {order_data["status"]}</p>
          </body>
        </html>
        """
        send_email(owner_subject, "FLAREN Owner", OWNER_EMAIL, owner_body_html)

        # Email to customer
        customer_subject = f"Order Placed – {order_id}"
        customer_body_html = f"""
        <html>
          <body>
            <h2>Order Placed Successfully</h2>
            <p>Hi {order_data["customer_name"]},</p>
            <p>Your order has been placed successfully.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Service:</strong> {order_data["service"]}</p>
            <p><strong>Description:</strong><br>{order_data["description"].replace("\n", "<br>")}</p>
            <p>We will contact you soon to confirm details.</p>
            <p><strong>Please check your email for further details.</strong></p>
            <p>— Team FLAREN</p>
          </body>
        </html>
        """
        send_email(customer_subject, order_data["customer_name"], order_data["email"], customer_body_html)

        flash("Order placed successfully. Please check your email for further details.", "success")
        return redirect(url_for("order_success", order_id=order_id))

    return render_template("order.html", services=SERVICES)

@app.route("/order-success")
def order_success():
    order_id = request.args.get("order_id", "")
    return render_template("order_success.html", order_id=order_id)

if __name__ == "__main__":
    app.run(debug=True)