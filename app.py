from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from ai_classifier_simple import classify_complaint
from database import save_complaint, resolve_complaint, get_complaint_by_token
from email_sender import send_department_email
import os

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🚀 APP.PY IS LOADING!")
print("=" * 60)

app = Flask(__name__)

# Twilio client
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Base URL for email links
BASE_URL = os.getenv("BASE_URL", "https://hostel-complaint-system-6yj2.onrender.com")

@app.route("/test", methods=["GET"])
def test():
    print("🧪 TEST ROUTE CALLED!")
    return "Test successful!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives WhatsApp messages from Twilio."""

    try:

        incoming_message = request.form.get("Body", "").strip()
        sender_phone = request.form.get("From", "")
        media_url = request.form.get("MediaUrl0", None)

        print(f"\n📨 New message from {sender_phone}")
        print(f"📝 Message: {incoming_message}")
        print(f"📷 Media: {media_url}")

        response = MessagingResponse()

        # Validate message
        if not incoming_message and not media_url:
            response.message("Please send a complaint message.")
            return str(response)

        # Step 1: Classify complaint using Groq
        print("🤖 Classifying complaint...")
        ai_result = classify_complaint(incoming_message, media_url)

        category = ai_result.get("category", "OTHER")
        priority = ai_result.get("priority", "MEDIUM")
        department_email = ai_result.get(
            "department_email",
            "admin@university.edu"
        )

        print(f"   Category: {category}, Priority: {priority}")

        # Step 2: Save to database
        print("💾 Saving to database...")
        saved = save_complaint(
            sender_phone,
            incoming_message,
            ai_result
        )

        if saved:

            complaint_id = str(saved["id"])[:8].upper()
            print(f"✅ Saved! ID: {complaint_id}")

            # Step 3: Send email to department
            print(f"📧 Sending email to {saved['department_email']}...")

            email_sent = send_department_email(saved, BASE_URL)

            if email_sent:
                print("✅ Email sent successfully!")
            else:
                print("⚠️ Email failed but complaint is saved")

            # Step 4: Reply to student via WhatsApp
            response.message(
                f"✅ Complaint Received!\n\n"
                f"📋 ID: #{complaint_id}\n"
                f"🏷️ Category: {category}\n"
                f"⚡ Priority: {priority}\n"
                f"🏢 Assigned to: {department_email}\n\n"
                f"You will be notified on WhatsApp once resolved.\n"
                f"Thank you!"
            )

        else:

            print("❌ Failed to save to database")

            response.message(
                "⚠️ Complaint received but could not be saved."
            )

        return str(response)

    except Exception as e:

        print("❌ Webhook error:", e)

        response = MessagingResponse()
        response.message(
            "⚠️ System error occurred. Please try again."
        )

        return str(response)


@app.route("/resolve", methods=["GET"])
def resolve():
    """Department clicks this link to resolve complaint."""
    token = request.args.get("token")
    note = request.args.get("note", "Issue has been resolved.")

    if not token:
        return "❌ Invalid link.", 400

    complaint = get_complaint_by_token(token)

    if not complaint:
        return "❌ Complaint not found.", 404

    if complaint["status"] == "RESOLVED":
        return "✅ This complaint was already resolved.", 200

    # Mark as resolved
    updated = resolve_complaint(token, note)

    if updated:
        # Send WhatsApp notification to student
        try:
            print(f"📲 Sending resolution notification to {complaint['student_phone']}")
            twilio_client.messages.create(
                from_=os.getenv("TWILIO_WHATSAPP_NUMBER"),
                to=complaint["student_phone"],
                body=(
                    f"✅ Great news!\n\n"
                    f"Your complaint #{str(complaint['id'])[:8].upper()} has been resolved!\n\n"
                    f"🏷️ Issue: {complaint.get('summary', complaint.get('category'))}\n"
                    f"🏢 Resolved by: {complaint.get('department_email')}\n\n"
                    f"Thank you for reporting. — Hostel Management"
                )
            )
            print("✅ Resolution notification sent!")
        except Exception as e:
            print(f"⚠️ WhatsApp notification failed: {e}")

        return f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0fdf4;">
            <div style="max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                <div style="font-size: 60px;">✅</div>
                <h1 style="color: #16a34a;">Complaint Resolved!</h1>
                <p style="color: #64748b;">The student has been notified via WhatsApp.</p>
                <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
                <p><b>Category:</b> {complaint['category']}</p>
                <p><b>Student:</b> {complaint['student_phone']}</p>
                <p><b>Issue:</b> {complaint.get('summary', '')}</p>
            </div>
        </body>
        </html>
        """, 200

    return "❌ Something went wrong.", 500


@app.route("/complaints", methods=["GET"])
def view_complaints():
    """View all complaints."""
    from database import get_all_complaints
    complaints = get_all_complaints()
    return jsonify(complaints), 200


@app.route("/", methods=["GET"])
def home():
    return "🏠 Hostel Complaint System is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)