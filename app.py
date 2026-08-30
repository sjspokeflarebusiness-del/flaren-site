from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import os
import random
import smtplib
import string

import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)


app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "flaren-secret-key-change-in-production",
)


# ============================================================
# CONFIGURATION
# ============================================================

OWNER_EMAIL = "sjspokeflarebusiness@gmail.com"
OWNER_PHONE = "8838969397"

APPS_SCRIPT_WEBHOOK_URL = os.getenv(
    "APPS_SCRIPT_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbzu3DUX5GsVlGNz5ts01dkZ6Vq7B9Wozr4BcP2iSr7mbF5vbCac27niA9_w66P3S7fOOw/exec",
)

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or OWNER_EMAIL)


# ============================================================
# SERVICES
# ============================================================

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


# ============================================================
# SAMPLE WORK DATA
# ============================================================

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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean(value):
    return (value or "").strip()


def html_text(value):
    return escape(clean(value)).replace("\n", "<br>")


def generate_order_id():
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=4,
        )
    )
    return f"FLR-{date_part}-{random_part}"


def generate_contact_id():
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=4,
        )
    )
    return f"CNT-{date_part}-{random_part}"


def send_to_sheets(payload):
    if not APPS_SCRIPT_WEBHOOK_URL:
        app.logger.warning("APPS_SCRIPT_WEBHOOK_URL is empty.")
        return False

    try:
        response = requests.post(
            APPS_SCRIPT_WEBHOOK_URL,
            json=payload,
            timeout=20,
        )

        if not 200 <= response.status_code < 300:
            app.logger.error(
                "Apps Script returned HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
            return False

        try:
            result = response.json()

            if result.get("success") is False:
                app.logger.error(
                    "Apps Script returned an error: %s",
                    result.get("error"),
                )
                return False

        except ValueError:
            app.logger.warning(
                "Apps Script response was not JSON: %s",
                response.text[:500],
            )

        return True

    except requests.RequestException as error:
        app.logger.error("Could not reach Apps Script: %s", error)
        return False


def send_email(recipient_email, subject, body_html):
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASS:
        app.logger.warning(
            "SMTP is not configured. Email was not sent."
        )
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = recipient_email
    message.attach(
        MIMEText(body_html, "html", "utf-8")
    )

    try:
        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20,
        ) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(message)

        return True

    except (smtplib.SMTPException, OSError) as error:
        app.logger.error("SMTP email failed: %s", error)
        return False


# ============================================================
# HOME
# ============================================================

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


# ============================================================
# SERVICES AND PROCESS
# ============================================================

@app.route("/services")
def services():
    return render_template(
        "services.html",
        services=SERVICES,
    )


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/process")
def process():
    return render_template("process.html")


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():
    return render_template("about.html")


# ============================================================
# INTERACTIVE WORK / PROJECT PLANNER
# ============================================================

@app.route("/work", methods=["GET", "POST"])
def work():
    recommendation = None

    if request.method == "POST":
        goal = clean(request.form.get("goal"))
        audience = clean(request.form.get("audience"))
        deadline = clean(request.form.get("deadline"))

        recommendations = {
            "event": {
                "service": "Poster designs or Invitations",
                "reason": (
                    "These services are suitable for promoting an event "
                    "or sharing event details clearly."
                ),
                "next_step": (
                    "Prepare the event name, date, venue, theme, colors, "
                    "and required size."
                ),
            },
            "business": {
                "service": (
                    "Logo Design, Advertisement Posters, "
                    "or Simple Website"
                ),
                "reason": (
                    "These services can help your business look more "
                    "professional and communicate its offer."
                ),
                "next_step": (
                    "Prepare your business name, audience, services, "
                    "preferred style, and deadline."
                ),
            },
            "school": {
                "service": (
                    "School Project Designs or Presentation Designs"
                ),
                "reason": (
                    "These services help organize information into a "
                    "polished academic project."
                ),
                "next_step": (
                    "Prepare the topic, number of pages or slides, "
                    "instructions, and submission date."
                ),
            },
            "personal": {
                "service": (
                    "Wallpapers, Invitations, or Custom Digital Work"
                ),
                "reason": (
                    "These services can be adapted for personal events, "
                    "gifts, profiles, and creative ideas."
                ),
                "next_step": (
                    "Prepare your idea, preferred colors, reference images, "
                    "and final size."
                ),
            },
            "website": {
                "service": "Simple Website",
                "reason": (
                    "A simple website can present your work, services, "
                    "contact information, or personal profile online."
                ),
                "next_step": (
                    "Prepare the website purpose, required pages, "
                    "examples you like, and deadline."
                ),
            },
        }

        recommendation = recommendations.get(
            goal,
            {
                "service": "Custom Digital Work",
                "reason": (
                    "Your project may need a custom solution based on "
                    "its exact requirements."
                ),
                "next_step": (
                    "Tell us your idea, preferred style, audience, "
                    "and deadline."
                ),
            },
        )

        recommendation["goal"] = goal
        recommendation["audience"] = audience
        recommendation["deadline"] = deadline

    return render_template(
        "work.html",
        recommendation=recommendation,
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = clean(request.form.get("contactName"))
        email = clean(request.form.get("contactEmail"))
        message = clean(request.form.get("contactMessage"))

        if not name or not email or not message:
            flash(
                "Please complete your name, email, and message.",
                "error",
            )
            return redirect(url_for("contact"))

        contact_id = generate_contact_id()

        contact_data = {
            "type": "contact",
            "contact_id": contact_id,
            "date": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "message": message,
            "status": "New",
        }

        sheets_sent = send_to_sheets(contact_data)

        owner_subject = (
            f"FLAREN — New Contact Message: {contact_id}"
        )

        owner_body_html = f"""
        <html>
          <body>
            <h2>New FLAREN Contact Message</h2>
            <p>
              <strong>Contact ID:</strong>
              {escape(contact_id)}
            </p>
            <p>
              <strong>Name:</strong>
              {html_text(name)}
            </p>
            <p>
              <strong>Email:</strong>
              {html_text(email)}
            </p>
            <p><strong>Message:</strong></p>
            <p>{html_text(message)}</p>
          </body>
        </html>
        """

        owner_email_sent = send_email(
            OWNER_EMAIL,
            owner_subject,
            owner_body_html,
        )

        customer_subject = (
            f"FLAREN — Message Received: {contact_id}"
        )

        customer_body_html = f"""
        <html>
          <body>
            <h2>Thank you for contacting FLAREN</h2>
            <p>Hi {html_text(name)},</p>
            <p>
              We received your message successfully and will get back
              to you soon.
            </p>
            <p>
              <strong>Reference ID:</strong>
              {escape(contact_id)}
            </p>
            <p><strong>Your message:</strong></p>
            <p>{html_text(message)}</p>
            <p>— Team FLAREN</p>
          </body>
        </html>
        """

        customer_email_sent = send_email(
            email,
            customer_subject,
            customer_body_html,
        )

        if sheets_sent or owner_email_sent or customer_email_sent:
            flash(
                "Your message was sent successfully. "
                "We will contact you soon.",
                "success",
            )
        else:
            flash(
                "Your message could not be delivered. "
                "Please try again later.",
                "error",
            )

        return redirect(url_for("contact"))

    return render_template(
        "contact.html",
        owner_email=OWNER_EMAIL,
        owner_phone=OWNER_PHONE,
    )


# ============================================================
# ORDERS
# ============================================================

@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        data = request.form
        order_id = generate_order_id()

        order_data = {
            "type": "order",
            "order_id": order_id,
            "date": datetime.now().isoformat(),
            "customer_name": clean(
                data.get("customerName")
            ),
            "email": clean(
                data.get("email")
            ),
            "phone": clean(
                data.get("phone")
            ),
            "service": clean(
                data.get("service")
            ),
            "budget": clean(
                data.get("budget")
            ),
            "description": clean(
                data.get("description")
            ),
            "deadline": clean(
                data.get("deadline")
            ),
            "reference_link": clean(
                data.get("referenceLink")
            ),
            "reference_file": clean(
                data.get("referenceFile")
            ),
            "additional_requirements": clean(
                data.get("additionalRequirements")
            ),
            "status": "New",
        }

        if not order_data["customer_name"]:
            flash("Please enter your name.", "error")
            return redirect(url_for("order"))

        if not order_data["email"]:
            flash("Please enter your email.", "error")
            return redirect(url_for("order"))

        if not order_data["service"]:
            flash("Please choose a service.", "error")
            return redirect(url_for("order"))

        if not order_data["description"]:
            flash(
                "Please describe your project.",
                "error",
            )
            return redirect(url_for("order"))

        sheets_sent = send_to_sheets(order_data)

        owner_subject = (
            f"FLAREN — New Order: {order_id}"
        )

        owner_body_html = f"""
        <html>
          <body>
            <h2>New FLAREN Order</h2>

            <p>
              <strong>Order ID:</strong>
              {escape(order_id)}
            </p>

            <p>
              <strong>Date:</strong>
              {escape(order_data["date"])}
            </p>

            <p>
              <strong>Customer:</strong>
              {html_text(order_data["customer_name"])}
            </p>

            <p>
              <strong>Email:</strong>
              {html_text(order_data["email"])}
            </p>

            <p>
              <strong>Phone:</strong>
              {html_text(order_data["phone"])}
            </p>

            <p>
              <strong>Service:</strong>
              {html_text(order_data["service"])}
            </p>

            <p>
              <strong>Budget:</strong>
              {html_text(order_data["budget"]) or "Not specified"}
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
              <strong>Reference file:</strong>
              {html_text(order_data["reference_file"]) or "None"}
            </p>

            <p>
              <strong>Description:</strong><br>
              {html_text(order_data["description"])}
            </p>

            <p>
              <strong>Additional requirements:</strong><br>
              {
                  html_text(
                      order_data["additional_requirements"]
                  )
                  or "None"
              }
            </p>

            <p>
              <strong>Status:</strong>
              New
            </p>
          </body>
        </html>
        """

        owner_email_sent = send_email(
            OWNER_EMAIL,
            owner_subject,
            owner_body_html,
        )

        customer_subject = (
            f"FLAREN — Order Confirmed: {order_id}"
        )

        customer_body_html = f"""
        <html>
          <body>
            <h2>Order Placed Successfully</h2>

            <p>
              Hi {html_text(order_data["customer_name"])},
            </p>

            <p>
              Thank you for choosing FLAREN. Your order has been
              received successfully.
            </p>

            <p>
              <strong>Order ID:</strong>
              {escape(order_id)}
            </p>

            <p>
              <strong>Service:</strong>
              {html_text(order_data["service"])}
            </p>

            <p>
              We will contact you soon to confirm the details.
            </p>

            <p>— Team FLAREN</p>
          </body>
        </html>
        """

        customer_email_sent = False

        if order_data["email"]:
            customer_email_sent = send_email(
                order_data["email"],
                customer_subject,
                customer_body_html,
            )

        if (
            sheets_sent
            or owner_email_sent
            or customer_email_sent
        ):
            flash(
                "Order placed successfully. "
                "Please check your email for details.",
                "success",
            )
        else:
            flash(
                "The order could not be delivered. "
                "Please try again later.",
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
    order_id = clean(
        request.args.get("order_id")
    )

    return render_template(
        "order_success.html",
        order_id=order_id,
    )


# ============================================================
# WORK DETAIL PAGES
# ============================================================

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


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.exception(
        "Unhandled server error: %s",
        error,
    )

    return render_template("500.html"), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
