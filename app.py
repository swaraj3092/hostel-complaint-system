from flask import Flask, request, jsonify
from dotenv import load_dotenv
from ai_classifier import classify_complaint
from database import save_complaint, resolve_complaint, get_complaint_by_token
from email_sender import send_department_email
import os
import requests
import json

load_dotenv()

app = Flask(__name__)

META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")

# ⚠️ Update this after deploying to Render!
BASE_URL = os.getenv("BASE_URL", "https://roxanne-fervid-nonstoically.ngrok-free.dev")


def send_whatsapp_message(to_number, message):
    """Send WhatsApp message using Meta API."""
    url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"✅ WhatsApp message sent to {to_number}")
        return True
    else:
        print(f"❌ WhatsApp send failed: {response.text}")
        return False


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Meta calls this once to verify your webhook URL.
    This is different from Twilio — Meta requires verification.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        print("✅ Webhook verified by Meta!")
        return challenge, 200
    else:
        print("❌ Webhook verification failed")
        return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives WhatsApp messages from students via Meta API."""
    
    try:
        data = request.get_json()
        
        # Navigate Meta's nested JSON structure
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return "ok", 200
        
        message = messages[0]
        
        # Extract message details
        sender_phone = message.get("from")
        message_type = message.get("type")
        
        if message_type == "text":
            incoming_message = message.get("text", {}).get("body", "").strip()
        else:
            # Handle non-text messages
            send_whatsapp_message(
                sender_phone,
                "Please send your complaint as a text message. You can also describe the issue in words."
            )
            return "ok", 200
        
        print(f"\n📨 New message from {sender_phone}")
        print(f"📝 Message: {incoming_message}")
        
        if incoming_message:
            # Step 1: Classify with ML
            ai_result = classify_complaint(incoming_message)
            
            # Step 2: Save to database
            saved = save_complaint(sender_phone, incoming_message, ai_result)
            
            if saved:
                complaint_id = str(saved["id"])[:8].upper()
                
                # Step 3: Send email to department
                email_sent = send_department_email(saved, BASE_URL)
                
                # Step 4: Send acknowledgement to student
                send_whatsapp_message(
                    sender_phone,
                    f"✅ Complaint Received!\n\n"
                    f"📋 ID: #{complaint_id}\n"
                    f"🏷️ Category: {ai_result.get('category')}\n"
                    f"⚡ Priority: {ai_result.get('priority')}\n"
                    f"🏢 Assigned to: {ai_result.get('department_email')}\n\n"
                    f"You will be notified on WhatsApp once resolved. Thank you!"
                )
            else:
                send_whatsapp_message(
                    sender_phone,
                    "✅ Complaint received! Our team will look into it shortly."
                )
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
    
    return "ok", 200


@app.route("/resolve", methods=["GET"])
def resolve():
    """Department clicks this to mark complaint as resolved."""
    token = request.args.get("token")
    note = request.args.get("note", "Issue has been resolved.")

    if not token:
        return "❌ Invalid link.", 400

    complaint = get_complaint_by_token(token)

    if not complaint:
        return "❌ Complaint not found.", 404

    if complaint["status"] == "RESOLVED":
        return "✅ Already resolved.", 200

    updated = resolve_complaint(token, note)

    if updated:
        # Notify student on WhatsApp
        send_whatsapp_message(
            complaint["student_phone"],
            f"✅ Great news!\n\n"
            f"Your complaint #{str(complaint['id'])[:8].upper()} has been resolved!\n\n"
            f"🏷️ Issue: {complaint.get('summary', complaint.get('category'))}\n"
            f"🏢 Resolved by: {complaint.get('department_email')}\n\n"
            f"Thank you for reporting. — Hostel Management"
        )

        return f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0fdf4;">
            <div style="max-width:500px; margin:0 auto; background:white; padding:40px; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                <div style="font-size:60px;">✅</div>
                <h1 style="color:#16a34a;">Complaint Resolved!</h1>
                <p style="color:#64748b;">The student has been notified via WhatsApp.</p>
                <hr style="border:1px solid #e2e8f0; margin:20px 0;">
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
