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
    send_from_directory,
    url_for,
)


app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "flaren-secret-key-change-in-production",
)

app.config["TEMPLATES_AUTO_RELOAD"] = False


# ============================================================
# CONFIGURATION
# ============================================================

SITE_URL = os.getenv(
    "SITE_URL",
    "https://flaren-site.onrender.com",
).rstrip("/")

OWNER_EMAIL = os.getenv(
    "OWNER_EMAIL",
    "sjspokeflarebusiness@gmail.com",
)

OWNER_PHONE = os.getenv(
    "OWNER_PHONE",
    "8838969397",
)

APPS_SCRIPT_WEBHOOK_URL = os.getenv(
    "APPS_SCRIPT_WEBHOOK_URL",
    "https://script.google.com/macros/s/"
    "AKfycbzu3DUX5GsVlGNz5ts01dkZ6Vq7B9Wozr4BcP2iSr7mbF5vbCac27niA9_w66P3S7fOOw"
    "/exec",
)

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv(
    "SMTP_FROM",
    SMTP_USER or OWNER_EMAIL,
)


# ============================================================
# FLAREN V2 SERVICE STRUCTURE
# ============================================================

SERVICE_CATEGORIES = [
    {
        "key": "design",
        "title": "Design Studio",
        "description": (
            "Professional visual design for events, businesses, "
            "students, creators, and personal projects."
        ),
        "items": [
            "Posters and advertisements",
            "Social-media creatives",
            "Invitations and cards",
            "Logos and basic branding",
            "Menus and certificates",
            "Wallpapers and digital artwork",
        ],
    },
    {
        "key": "websites",
        "title": "Website Studio",
        "description": (
            "Simple responsive websites that help people present "
            "their work, services, products, or business online."
        ),
        "items": [
            "Personal portfolios",
            "Student portfolios",
            "Business websites",
            "Landing pages",
            "Event pages",
            "Digital business cards",
            "Link-in-bio pages",
            "Website redesigns",
        ],
    },
    {
        "key": "qr",
        "title": "QR and Smart Digital",
        "description": (
            "Useful digital links and QR experiences for sharing "
            "menus, portfolios, contact details, and events."
        ),
        "items": [
            "QR menus",
            "QR business cards",
            "QR portfolios",
            "QR WhatsApp links",
            "QR event pages",
            "Digital contact cards",
            "QR feedback links",
        ],
    },
    {
        "key": "education",
        "title": "Student and Education",
        "description": (
            "Clear visual support for student presentations, "
            "projects, educational events, and learning materials."
        ),
        "items": [
            "Project covers",
            "Presentation design",
            "Educational diagrams",
            "Infographics",
            "Certificates",
            "School event materials",
            "Competition posters",
        ],
    },
]


# Backward-compatible service list for the existing order form.
SERVICES = [
    "Poster or advertisement design",
    "Social-media creative",
    "Invitation or card design",
    "Logo or basic branding",
    "Menu or certificate design",
    "Wallpaper or digital artwork",
    "Personal portfolio website",
    "Student portfolio website",
    "Business website",
    "Landing page",
    "Event website",
    "Digital business card",
    "QR menu or QR business card",
    "QR portfolio or QR event page",
    "School project design",
    "Presentation design",
    "Educational diagram or infographic",
    "Custom digital work",
]


# ============================================================
# PACKAGES
# ============================================================

PACKAGES = [
    {
        "key": "starter",
        "name": "FLAREN Starter",
        "category": "Branding",
        "short_description": (
            "A simple starting identity for an individual, "
            "creator, or small business."
        ),
        "includes": [
            "Simple logo concept",
            "Brand color direction",
            "Business card or digital profile graphic",
            "One revision round",
            "Final files in agreed formats",
        ],
        "price": "Starting price confirmed after requirements",
        "cta": "Start with Starter",
    },
    {
        "key": "promote",
        "name": "FLAREN Promote",
        "category": "Marketing Design",
        "short_description": (
            "A practical creative package for an event, offer, "
            "product, shop, or announcement."
        ),
        "includes": [
            "One main promotional poster",
            "Two social-media or WhatsApp versions",
            "Clear call-to-action layout",
            "QR code when required",
            "One revision round",
        ],
        "price": "Starting price confirmed after requirements",
        "cta": "Choose Promote",
    },
    {
        "key": "digital",
        "name": "FLAREN Digital",
        "category": "Website and Digital Presence",
        "short_description": (
            "A simple online presence for a person, event, creator, "
            "or small business."
        ),
        "includes": [
            "One-page responsive landing page",
            "Contact or WhatsApp button",
            "Customer-provided text and images",
            "Clear call-to-action section",
            "One revision round",
        ],
        "price": "Starting price confirmed after requirements",
        "cta": "Choose Digital",
    },
    {
        "key": "custom",
        "name": "FLAREN Custom",
        "category": "Custom Project",
        "short_description": (
            "For ideas that need a combination of design, website, "
            "QR, education, or digital work."
        ),
        "includes": [
            "Project requirements review",
            "Recommended approach",
            "Custom scope and quote",
            "Confirmed timeline",
            "Agreed revision plan",
        ],
        "price": "Quote after project review",
        "cta": "Discuss a Custom Project",
    },
]


# ============================================================
# SAMPLE WORK DATA
# ============================================================

SAMPLE_WORKS = [
    {
        "key": "logo",
        "title": "FLAREN Logo Design",
        "desc": "A bold visual identity created for the FLAREN brand.",
        "image": "logo.png",
        "price": "₹499",
        "category": "Branding",
        "delivery": "1–2 days",
        "details": (
            "A clean logo concept designed to make a brand look "
            "memorable and professional."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The brand needed a memorable visual identity that "
            "could work across digital platforms."
        ),
        "solution": (
            "A bold logo direction with a strong symbol and "
            "clear brand presentation."
        ),
    },
    {
        "key": "personal_portfolio",
        "title": "Personal Portfolio Design",
        "desc": "A polished visual portfolio for personal creative work.",
        "image": "portfolio-1.png",
        "price": "₹499",
        "category": "Portfolio Design",
        "delivery": "1–2 days",
        "details": (
            "A simple and attractive portfolio layout for showcasing "
            "photography, creative work, or personal projects."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The work needed a clear structure for presenting "
            "personal creative projects."
        ),
        "solution": (
            "A clean portfolio layout focused on visual work and "
            "easy navigation."
        ),
    },
    {
        "key": "advertisement_posters",
        "title": "Advertisement Poster",
        "desc": (
            "A promotional poster designed for events and "
            "small businesses."
        ),
        "image": "portfolio-2.png",
        "price": "₹399",
        "category": "Poster Design",
        "delivery": "1–2 days",
        "details": (
            "A clear promotional design suitable for social media, "
            "WhatsApp sharing, printing, or local advertising."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The main offer and contact information needed to be "
            "understood quickly."
        ),
        "solution": (
            "A clear promotional layout with a visible message "
            "and call to action."
        ),
    },
    {
        "key": "digital_images",
        "title": "Digital Social Media Design",
        "desc": (
            "Digital artwork, banners, and social-media graphics."
        ),
        "image": "portfolio-3.png",
        "price": "₹299",
        "category": "Digital Design",
        "delivery": "1–2 days",
        "details": (
            "A custom digital image created for online promotion, "
            "social media, announcements, or personal use."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The design needed to communicate clearly in a "
            "digital-first format."
        ),
        "solution": (
            "A visual graphic adapted for online sharing and "
            "social-media presentation."
        ),
    },
    {
        "key": "card_designs",
        "title": "Website Design",
        "desc": (
            "A simple website concept for a personal brand "
            "or small business."
        ),
        "image": "portfolio-4.png",
        "price": "₹4,999",
        "category": "Website Design",
        "delivery": "3–5 days",
        "details": (
            "A simple responsive website with useful sections, "
            "contact information, and a clear call to action."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The website needed to present information clearly "
            "without unnecessary complexity."
        ),
        "solution": (
            "A responsive structure with focused content, "
            "contact options, and a clear next step."
        ),
    },
    {
        "key": "awesome_posters",
        "title": "Card Design Collection",
        "desc": (
            "Business cards, greeting cards, and invitation "
            "card designs."
        ),
        "image": "portfolio-5.png",
        "price": "₹399",
        "category": "Card Design",
        "delivery": "1–2 days",
        "details": (
            "Custom card designs suitable for business cards, "
            "greetings, celebrations, invitations, and online sharing."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The card needed to balance useful information with "
            "a visually attractive presentation."
        ),
        "solution": (
            "A clean card layout suitable for digital sharing "
            "or final export."
        ),
    },
    {
        "key": "extra_work",
        "title": "Featured Creative Work",
        "desc": (
            "A selection of custom digital work from different "
            "project types."
        ),
        "image": "portfolio-6.png",
        "price": "₹499",
        "category": "Custom Design",
        "delivery": "1–3 days",
        "details": (
            "Flexible digital work created according to the "
            "client’s specific idea, style, and requirements."
        ),
        "project_type": "Concept project",
        "challenge": (
            "The project required a flexible approach based on "
            "the customer’s specific idea."
        ),
        "solution": (
            "A custom digital direction shaped around the "
            "requested style and purpose."
        ),
    },
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean(value):
    """Return a trimmed string."""
    return (value or "").strip()


def html_text(value):
    """Escape text before placing it inside an HTML email."""
    return escape(clean(value)).replace("\n", "<br>")


def generate_reference_id(prefix):
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=4,
        )
    )
    return f"{prefix}-{date_part}-{random_part}"


def generate_order_id():
    return generate_reference_id("FLR")


def generate_contact_id():
    return generate_reference_id("CNT")


def send_to_sheets(payload):
    """Send order/contact data to Google Apps Script."""
    if not APPS_SCRIPT_WEBHOOK_URL:
        app.logger.warning(
            "APPS_SCRIPT_WEBHOOK_URL is empty."
        )
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
        app.logger.error(
            "Could not reach Apps Script: %s",
            error,
        )
        return False


def send_email(recipient_email, subject, body_html):
    """Send an HTML email using SMTP."""
    if not recipient_email:
        return False

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
        MIMEText(
            body_html,
            "html",
            "utf-8",
        )
    )

    try:
        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=20,
        ) as server:
            server.starttls()
            server.login(
                SMTP_USER,
                SMTP_PASS,
            )
            server.send_message(message)

        return True

    except (
        smtplib.SMTPException,
        OSError,
    ) as error:
        app.logger.error(
            "SMTP email failed: %s",
            error,
        )
        return False


def selected_service_exists(value):
    return clean(value) in SERVICES


# ============================================================
# GLOBAL TEMPLATE CONTEXT
# ============================================================

@app.context_processor
def inject_global_template_values():
    return {
        "current_year": datetime.now().year,
        "site_url": SITE_URL,
        "owner_email": OWNER_EMAIL,
        "owner_phone": OWNER_PHONE,
        "service_categories": SERVICE_CATEGORIES,
        "packages": PACKAGES,
    }


# ============================================================
# FAVICON
# ============================================================

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(
            app.root_path,
            "static",
        ),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# ============================================================
# SEO FILES
# ============================================================

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(
        os.path.join(
            app.root_path,
            "static",
        ),
        "robots.txt",
        mimetype="text/plain",
    )


@app.route("/sitemap.xml")
def sitemap_xml():
    return send_from_directory(
        os.path.join(
            app.root_path,
            "static",
        ),
        "sitemap.xml",
        mimetype="application/xml",
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "FLAREN",
    }, 200


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template(
        "home.html",
        sample_works=SAMPLE_WORKS,
        service_categories=SERVICE_CATEGORIES,
        packages=PACKAGES,
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
        service_categories=SERVICE_CATEGORIES,
        packages=PACKAGES,
    )


@app.route("/how-it-works")
def how_it_works():
    return render_template(
        "how_it_works.html",
        packages=PACKAGES,
    )


@app.route("/process")
def process():
    return render_template(
        "process.html",
        packages=PACKAGES,
    )


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
                "service": (
                    "Posters, Advertisements, or Invitations"
                ),
                "reason": (
                    "These services are suitable for promoting an "
                    "event or sharing event details clearly."
                ),
                "next_step": (
                    "Prepare the event name, date, venue, theme, "
                    "colors, and required size."
                ),
            },
            "business": {
                "service": (
                    "FLAREN Starter, FLAREN Promote, FLAREN Digital, "
                    "or a custom business project"
                ),
                "reason": (
                    "These options can help your business look more "
                    "professional and communicate its offer."
                ),
                "next_step": (
                    "Prepare your business name, audience, services, "
                    "preferred style, and deadline."
                ),
            },
            "school": {
                "service": (
                    "School Project Design or Presentation Design"
                ),
                "reason": (
                    "These services help organize information into "
                    "a polished academic project."
                ),
                "next_step": (
                    "Prepare the topic, number of pages or slides, "
                    "instructions, and submission date."
                ),
            },
            "personal": {
                "service": (
                    "Wallpaper, Invitation, Portfolio, or "
                    "Custom Digital Work"
                ),
                "reason": (
                    "These services can be adapted for personal "
                    "events, gifts, profiles, and creative ideas."
                ),
                "next_step": (
                    "Prepare your idea, preferred colors, reference "
                    "images, and final size."
                ),
            },
            "website": {
                "service": (
                    "FLAREN Digital or Simple Website"
                ),
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
                "service": "FLAREN Custom",
                "reason": (
                    "Your project may need a custom solution based "
                    "on its exact requirements."
                ),
                "next_step": (
                    "Tell us your idea, preferred style, audience, "
                    "and deadline."
                ),
            },
        ).copy()

        recommendation["goal"] = goal
        recommendation["audience"] = audience
        recommendation["deadline"] = deadline

    return render_template(
        "work.html",
        recommendation=recommendation,
        packages=PACKAGES,
        service_categories=SERVICE_CATEGORIES,
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
              We received your message successfully and will get
              back to you soon.
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

        if (
            sheets_sent
            or owner_email_sent
            or customer_email_sent
        ):
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
            "package": clean(
                data.get("package")
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
            flash(
                "Please enter your name.",
                "error",
            )
            return redirect(url_for("order"))

        if not order_data["email"]:
            flash(
                "Please enter your email.",
                "error",
            )
            return redirect(url_for("order"))

        if not order_data["service"]:
            flash(
                "Please choose a service.",
                "error",
            )
            return redirect(url_for("order"))

        if not selected_service_exists(
            order_data["service"]
        ):
            flash(
                "Please choose a valid service option.",
                "error",
            )
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
              {html_text(
                  order_data["customer_name"]
              )}
            </p>

            <p>
              <strong>Email:</strong>
              {html_text(
                  order_data["email"]
              )}
            </p>

            <p>
              <strong>Phone:</strong>
              {html_text(
                  order_data["phone"]
              )}
            </p>

            <p>
              <strong>Service:</strong>
              {html_text(
                  order_data["service"]
              )}
            </p>

            <p>
              <strong>Package:</strong>
              {html_text(
                  order_data["package"]
              ) or "Not specified"}
            </p>

            <p>
              <strong>Budget:</strong>
              {html_text(
                  order_data["budget"]
              ) or "Not specified"}
            </p>

            <p>
              <strong>Deadline:</strong>
              {html_text(
                  order_data["deadline"]
              ) or "Not specified"}
            </p>

            <p>
              <strong>Reference link:</strong>
              {html_text(
                  order_data["reference_link"]
              ) or "None"}
            </p>

            <p>
              <strong>Reference file:</strong>
              {html_text(
                  order_data["reference_file"]
              ) or "None"}
            </p>

            <p>
              <strong>Description:</strong><br>
              {html_text(
                  order_data["description"]
              )}
            </p>

            <p>
              <strong>Additional requirements:</strong><br>
              {
                  html_text(
                      order_data[
                          "additional_requirements"
                      ]
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
            f"FLAREN — Order Request Received: {order_id}"
        )

        customer_body_html = f"""
        <html>
          <body>
            <h2>FLAREN Project Request Received</h2>

            <p>
              Hi {html_text(
                  order_data["customer_name"]
              )},
            </p>

            <p>
              Thank you for choosing FLAREN. We received your
              project request successfully.
            </p>

            <p>
              <strong>Order ID:</strong>
              {escape(order_id)}
            </p>

            <p>
              <strong>Service:</strong>
              {html_text(
                  order_data["service"]
              )}
            </p>

            <p>
              FLAREN will review your details and contact you to
              confirm the final scope, price, and delivery time.
            </p>

            <p>
              Submitting this request does not automatically
              confirm a final price or start date.
            </p>

            <p>— Team FLAREN</p>
          </body>
        </html>
        """

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
                "Project request received successfully.",
                "success",
            )
        else:
            flash(
                "The project request could not be delivered. "
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
        packages=PACKAGES,
        service_categories=SERVICE_CATEGORIES,
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
        return render_template(
            "404.html"
        ), 404

    return render_template(
        "work_detail.html",
        work=selected_work,
        sample_works=SAMPLE_WORKS,
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.exception(
        "Unhandled server error: %s",
        error,
    )

    return render_template(
        "500.html"
    ), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    port = int(
        os.getenv(
            "PORT",
            "5000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
