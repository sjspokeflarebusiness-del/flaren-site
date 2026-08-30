from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import os
import random
import smtplib
import string

import requests


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "flaren-secret-key-change-in-production")


# =========================
# CONFIGURATION
# =========================

OWNER_EMAIL = "sjspokeflarebusiness@gmail.com"
OWNER_PHONE = "8838969397"

APPS_SCRIPT_WEBHOOK_URL = os.getenv(
    "APPS_SCRIPT_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbyHJBdGgYcIzCy9S0uzTuxl4kybB1f_3RgJJrIkh7UYvLz-yzJAPBsVuxOljAj0hadldQ/exec",
)

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or OWNER_EMAIL)


# =========================
# SITE DATA
# =========================

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

SAMPLE_WORKS = [
    {
        "key": "logo",
        "title": "Logo Design",
        "desc": "Our own FLAREN logo and branding visuals.",
        "image": "logo.png",
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


# =========================
# HELPERS
# =========================

def generate_order_id():
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"FLR-{date_part}-{random_part}"


def clean(value):
    return (value or "").strip()


def html_text(value):
    return escape(clean(value)).replace("\n", "<br>")


def send_to_sheets(payload):
    if not APPS_SCRIPT_WEBHOOK_URL:
        return False

    try:
        response = requests.post(
            APPS_SCRIPT_WEBHOOK_URL,
            json=payload,
            timeout=15,
        )
        return 200 <= response.status_code < 300
    except requests.RequestException:
        return False


def send_email(subject, recipient_email, body_html):
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASS:
        app.logger.warning("SMTP is not configured; email was not sent.")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = recipient_email
    message.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(message)

        return True

    except (smtplib.SMTPException, OSError) as error:
        app.logger.error("Email sending failed: %s", error)
        return False


def send_owner_and_user_contact_emails(name, email, message):
    safe_name = html_text(name)
    safe_email = html_text(email)
    safe_message = html_text(message)

    owner_subject = f"New contact enquiry from {name}"
    owner_body = f"""
    <html>
      <body>
        <h2>New Contact Enquiry</h2>
        <p><strong>Name:</strong> {safe_name}</p>
        <p><strong>Email:</strong> {safe_email}</p>
        <p><strong>Message:</strong></p>
        <p>{safe_message}</p>
      </body>
    </html>
    """

    owner_sent = send_email(
        owner_subject,
        OWNER_EMAIL,
        owner_body,
    )

    user_subject = "We received your message — FLAREN"
    user_body = f"""
    <html>
      <body>
        <h2>Thank you for contacting FLAREN</h2>
        <p>Hi {safe_name},</p>
        <p>
          We received your message and will get back to you soon.
        </p>
        <p><strong>Your message:</strong></p>
        <p>{safe_message}</p>
        <p>— Team FLAREN</p>
      </body>
    </html>
    """

    user_sent = send_email(
        user_subject,
        email,
        user_body,
    )

    return owner_sent and user_sent


# =========================
# MAIN PAGES
# =========================

@app.route("/")
def home():
    return render_template(
        "sample_works.html",
        sample_works=SAMPLE_WORKS,
    )


@app.route("/sample-works")
def sample_works():
    return render_template(
        "sample_works.html",
        sample_works=SAMPLE_WORKS,
    )


@app.route("/services")
def services():
    return render_template(
        "services.html",
        services=SERVICES,
    )


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/work")
def work():
    return render_template(
        "work.html",
        sample_works=SAMPLE_WORKS,
    )


@app.route("/process")
def process():
    return render_template("process.html")


@app.route("/about")
def about():
    return render_template("about.html")


# =========================
# CONTACT
# =========================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = clean(request.form.get("contactName"))
        email = clean(request.form.get("contactEmail"))
        message = clean(request.form.get("contactMessage"))

        if not name or not email or not message:
            flash("Please complete your name, email, and message.", "error")
            return redirect(url_for("contact"))

        contact_data = {
            "type": "contact",
            "date": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "message": message,
        }

        sheets_sent = send_to_sheets(contact_data)
        emails_sent = send_owner_and_user_contact_emails(
            name,
            email,
            message,
        )

        if emails_sent or sheets_sent:
            flash(
                "Your message was sent successfully. We will contact you soon.",
                "success",
            )
        else:
            flash(
                "Your message could not be delivered. Please try again later.",
                "error",
            )

        return redirect(url_for("contact"))

    return render_template(
        "contact.html",
        owner_email=OWNER_EMAIL,
        owner_phone=OWNER_PHONE,
    )


# =========================
# ORDERS
# =========================

@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        data = request.form
        order_id = generate_order_id()

        order_data = {
            "type": "order",
            "order_id": order_id,
            "date": datetime.now().isoformat(),
            "customer_name": clean(data.get("customerName")),
            "email": clean(data.get("email")),
            "phone": clean(data.get("phone")),
            "service": clean(data.get("service")),
            "description": clean(data.get("description")),
            "budget": clean(data.get("budget")),
            "deadline": clean(data.get("deadline")),
            "reference_link": clean(data.get("referenceLink")),
            "additional_requirements": clean(
                data.get("additionalRequirements")
            ),
            "status": "New",
        }

        sheets_sent = send_to_sheets(order_data)

        owner_subject = f"New Order — {order_id}"
        owner_body = f"""
        <html>
          <body>
            <h2>New Order Received</h2>
            <p><strong>Order ID:</strong> {escape(order_id)}</p>
            <p><strong>Date:</strong> {escape(order_data["date"])}</p>
            <p><strong>Customer:</strong> {html_text(order_data["customer_name"])}</p>
            <p><strong>Email:</strong> {html_text(order_data["email"])}</p>
            <p><strong>Phone:</strong> {html_text(order_data["phone"])}</p>
            <p><strong>Service:</strong> {html_text(order_data["service"])}</p>
            <p><strong>Budget:</strong> {html_text(order_data["budget"]) or "Not specified"}</p>
            <p>
              <strong>Description:</strong><br>
              {html_text(order_data["description"])}
            </p>
            <p>
              <strong>Deadline:</strong>
              {html_text(order_data["deadline"]) or "Not specified"}
            </p>
            <p>
              <strong>Reference link:</strong>
              {html_text(order_data["reference_link"]) or "None"}
            </p>
            <p>
              <strong>Additional requirements:</strong><br>
              {html_text(order_data["additional_requirements"]) or "None"}
            </p>
            <p><strong>Status:</strong> New</p>
          </body>
        </html>
        """

        owner_sent = send_email(
            owner_subject,
            OWNER_EMAIL,
            owner_body,
        )

        customer_subject = f"Order Placed — {order_id}"
        customer_body = f"""
        <html>
          <body>
            <h2>Order Placed Successfully</h2>
            <p>Hi {html_text(order_data["customer_name"])},</p>
            <p>Your order has been received successfully.</p>
            <p><strong>Order ID:</strong> {escape(order_id)}</p>
            <p><strong>Service:</strong> {html_text(order_data["service"])}</p>
            <p>
              We will contact you soon to confirm the details.
            </p>
            <p>— Team FLAREN</p>
          </body>
        </html>
        """

        customer_sent = send_email(
            customer_subject,
            order_data["email"],
            customer_body,
        )

        if sheets_sent or owner_sent or customer_sent:
            flash(
                "Order placed successfully. Please check your email for details.",
                "success",
            )
        else:
            flash(
                "The order could not be delivered. Please try again later.",
                "error",
            )

        return redirect(
            url_for(
                "order_success",
                order_id=order_id,
            )
        )

    return render_template(
        "order.html",
        services=SERVICES,
    )


@app.route("/order-success")
def order_success():
    order_id = clean(request.args.get("order_id"))
    return render_template(
        "order_success.html",
        order_id=order_id,
    )


# =========================
# WORK DETAIL
# =========================

@app.route("/work/<slug>")
def work_detail(slug):
    selected_work = next(
        (
            work_item
            for work_item in SAMPLE_WORKS
            if work_item["key"] == slug
        ),
        None,
    )

    if selected_work is None:
        return render_template("404.html"), 404

    return render_template(
        "work_detail.html",
        work=selected_work,
    )


# =========================
# ERROR HANDLER
# =========================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


# =========================
# LOCAL START
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
