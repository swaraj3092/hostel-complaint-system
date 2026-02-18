import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables safely
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Priority colors
PRIORITY_COLORS = {
    "URGENT": "#ef4444",
    "HIGH": "#f97316",
    "MEDIUM": "#eab308",
    "LOW": "#22c55e"
}

CATEGORY_ICONS = {
    "PLUMBING": "🔧",
    "ELECTRICAL": "⚡",
    "CLEANLINESS": "🧹",
    "SECURITY": "🔒",
    "WIFI": "📶",
    "FOOD": "🍽️",
    "FURNITURE": "🪑",
    "OTHER": "📋"
}


def send_department_email(complaint, resolve_base_url):
    """
    Send complaint email to department
    Works on both Localhost and Render
    """

    try:
        print("📧 Email function started")

        # Debug environment variables
        print("GMAIL_USER loaded:", bool(GMAIL_USER))
        print("GMAIL_APP_PASSWORD loaded:", bool(GMAIL_APP_PASSWORD))

        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            raise Exception("Missing Gmail environment variables")

        department_email = complaint.get("department_email")

        if not department_email:
            raise Exception("No department email found in complaint")

        resolve_link = f"{resolve_base_url}/resolve?token={complaint['resolve_token']}"

        priority = complaint.get("priority", "MEDIUM")
        category = complaint.get("category", "OTHER")

        priority_color = PRIORITY_COLORS.get(priority, "#eab308")
        category_icon = CATEGORY_ICONS.get(category, "📋")

        complaint_id = str(complaint["id"])[:8].upper()

        # Email HTML
        html_content = f"""
        <html>
        <body style="font-family: Arial; background:#f5f5f5; padding:20px;">
        
        <div style="background:white; padding:20px; border-radius:10px;">
        
        <h2>{category_icon} New Complaint #{complaint_id}</h2>

        <p><b>Priority:</b> 
        <span style="color:white; background:{priority_color}; padding:5px 10px; border-radius:5px;">
        {priority}
        </span>
        </p>

        <p><b>Student Phone:</b> {complaint.get("student_phone")}</p>

        <p><b>Message:</b></p>
        <p>{complaint.get("raw_message")}</p>

        <br>

        <a href="{resolve_link}" 
        style="background:#22c55e;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
        Mark as Resolved
        </a>

        </div>

        </body>
        </html>
        """

        # Build email
        msg = MIMEMultipart()
        msg["Subject"] = f"[{priority}] New Complaint #{complaint_id}"
        msg["From"] = GMAIL_USER
        msg["To"] = department_email

        msg.attach(MIMEText(html_content, "html"))

        print("Connecting to Gmail SMTP...")

        # SMTP connection
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

        print("Logging in...")

        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        print("Sending email...")

        server.sendmail(
            GMAIL_USER,
            department_email,
            msg.as_string()
        )

        server.quit()

        print(f"✅ Email sent successfully to {department_email}")

        return True

    except Exception as e:
        print("❌ EMAIL ERROR:", str(e))
        return False
