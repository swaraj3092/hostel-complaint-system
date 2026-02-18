from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from ai_classifier_simple import classify_complaint
from database import save_complaint, resolve_complaint, get_complaint_by_token
from email_sender import send_department_email
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Environment Variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
BASE_URL = os.getenv("BASE_URL")

# Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ================================
# WHATSAPP WEBHOOK
# ================================
BAASE_URL = os.getenv("BASE_URL")


@app.route("/webhook", methods=["POST"])
def webhook():
    print("\nWebhook triggered")
    print(request.form)

    incoming_message = request.form.get("Body", "").strip()
    sender_phone = request.form.get("From", "")
    media_url = request.form.get("MediaUrl0", None)

    response = MessagingResponse()

    # Always reply immediately to WhatsApp
    response.message("✅ Complaint received successfully!")

    # Process complaint AFTER reply is prepared
    try:
        print("Step 1: Classifying complaint...")
        ai_result = classify_complaint(incoming_message, media_url)
        print("AI result:", ai_result)

        print("Step 2: Saving complaint...")
        saved = save_complaint(sender_phone, incoming_message, ai_result)
        print("Saved result:", saved)

        if saved:
            print("Step 3: Sending email...")
            email_result = send_department_email(saved, os.getenv("BASE_URL"))
            print("Email result:", email_result)
        else:
            print("Save failed, email not sent.")

    except Exception as e:
        print("ERROR during processing:", str(e))

    return str(response)





# ================================
# RESOLVE ENDPOINT
# ================================
@app.route("/resolve", methods=["GET"])
def resolve():
    token = request.args.get("token")
    note = request.args.get("note", "Issue resolved.")

    if not token:
        return "❌ Invalid link.", 400

    complaint = get_complaint_by_token(token)

    if not complaint:
        return "❌ Complaint not found.", 404

    if complaint["status"] == "RESOLVED":
        return "✅ Already resolved.", 200

    updated = resolve_complaint(token, note)

    if updated:
        # Notify student via WhatsApp
        try:
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=complaint["student_phone"],
                body=(
                    f"✅ Great news!\n\n"
                    f"Your complaint #{str(complaint['id'])[:8].upper()} has been resolved!\n\n"
                    f"🏷️ Issue: {complaint.get('category')}\n"
                    f"🏢 Resolved by: {complaint.get('department_email')}\n\n"
                    f"Thank you for reporting. — Hostel Management"
                )
            )
            print("📲 Student notified via WhatsApp")
        except Exception as e:
            print("⚠️ WhatsApp notify failed:", str(e))

        return """
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: green;">✅ Complaint Resolved!</h1>
            <p>The student has been notified.</p>
        </body>
        </html>
        """

    return "❌ Something went wrong.", 500


# ================================
# ADMIN VIEW ALL COMPLAINTS
# ================================
@app.route("/complaints", methods=["GET"])
def view_complaints():
    from database import get_all_complaints
    complaints = get_all_complaints()
    return jsonify(complaints), 200


# ================================
# HOME ROUTE
# ================================
@app.route("/", methods=["GET"])
def home():
    return "🏠 Hostel Complaint System is running!", 200


# ================================
# RENDER DEPLOYMENT
# ================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
