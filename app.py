from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from ai_classifier_simple import classify_complaint
from database import save_complaint, resolve_complaint, get_complaint_by_token
from email_sender import send_department_email
import os

load_dotenv()

app = Flask(__name__)

# Twilio client for sending WhatsApp replies
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# ⚠️ Update this every time ngrok restarts!
BASE_URL = "https://roxanne-fervid-nonstoically.ngrok-free.dev"


@app.route("/webhook", methods=["POST"])
@app.route("/webhook", methods=["POST"])
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_message = request.form.get("Body", "").strip()
    sender_phone = request.form.get("From", "")

    response = MessagingResponse()

    try:
        ai_result = classify_complaint(incoming_message)
        saved = save_complaint(sender_phone, incoming_message, ai_result)

        if saved:
            response.message("✅ Complaint received successfully!")
        else:
            response.message("Complaint received.")

    except Exception as e:
        print("ERROR:", e)
        response.message("⚠️ Complaint received, but internal processing failed.")

    return str(response)




@app.route("/resolve", methods=["GET"])
def resolve():
    """Department clicks this link in email to resolve complaint."""
    token = request.args.get("token")
    note = request.args.get("note", "Issue has been resolved.")

    if not token:
        return "❌ Invalid link.", 400

    complaint = get_complaint_by_token(token)

    if not complaint:
        return "❌ Complaint not found.", 404

    if complaint["status"] == "RESOLVED":
        return "✅ This complaint was already resolved.", 200

    # Mark as resolved in database
    updated = resolve_complaint(token, note)

    if updated:
        # Send WhatsApp notification to student
        try:
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
            print(f"📲 WhatsApp notification sent to {complaint['student_phone']}")
        except Exception as e:
            print(f"⚠️ WhatsApp notify failed: {e}")

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
    """View all complaints — admin use."""
    from database import get_all_complaints
    complaints = get_all_complaints()
    return jsonify(complaints), 200


@app.route("/", methods=["GET"])
def home():
    return "🏠 Hostel Complaint System is running!", 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port,debug=True)