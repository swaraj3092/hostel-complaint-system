from flask import Flask, request, jsonify, session
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
from datetime import datetime
import time
import random

from database import (
    supabase,
    check_student_exists,
    register_student,
    get_student_by_phone,
    create_complaint,
    get_all_students,
    get_all_complaints,
    get_dashboard_stats,
    update_complaint_status,
    get_complaint_by_token
)
from ai_classifier import classify_complaint
from email_sender import send_department_email, send_whatsapp_notification

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fixxo-super-secret-key-change-in-production-2026")

# CORS Configuration with credentials support
CORS(app, 
     resources={r"/api/*": {"origins": ["http://localhost:3000", "https://hostel-complaint-system-1-r1g3.onrender.com"]}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint."""
    return "🏠 Fixxo API is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    try:
        incoming_msg = request.values.get("Body", "").strip()
        from_number = request.values.get("From", "")
        
        print("=" * 60)
        print("📱 INCOMING WHATSAPP MESSAGE")
        print(f"From: {from_number}")
        print(f"Message: {incoming_msg}")
        
        # Create Twilio response
        resp = MessagingResponse()
        msg = resp.message()
        
        # Check if student is registered
        student = check_student_exists(from_number)
        
        if not student:
            print(f"❌ Student not registered: {from_number}")
            # Send registration link
            base_url = os.getenv("BASE_URL", "http://localhost:3000")
            # Extract phone number without 'whatsapp:+' prefix
            phone = from_number.replace("whatsapp:+", "")
            registration_link = f"{base_url}/register?phone={phone}"
            
            msg.body(f"""👋 Welcome to Fixxo!

Please register first (one-time only):
🔗 {registration_link}

After registration, send your complaint again!""")
            
            print(f"✅ Registration link sent: {registration_link}")
            print("=" * 60)
            return str(resp)
        
        # Student is registered - process complaint
        print(f"✅ Student found: {student['student_name']}")
        print(f"   Hostel: {student['hostel_name']}")
        print(f"   Room: {student['room_number']}")
        
        # Classify the complaint using AI
        classification = classify_complaint(incoming_msg)
        print(f"🤖 AI Classification: {classification['category']} ({classification['priority']})")
        print(f"   Summary: {classification['summary']}")
        print(f"   Department: {classification['department_email']}")
        
        # Create complaint in database with ALL required arguments
        complaint = create_complaint(
            student_id=student['id'],
            student_phone=from_number,
            student_name=student['student_name'],
            hostel_name=student['hostel_name'],
            room_number=student['room_number'],
            category=classification['category'],
            priority=classification['priority'],
            raw_message=incoming_msg,
            summary=classification['summary'],
            department_email=classification['department_email'],
            confidence=classification['confidence']
        )
        
        if not complaint:
            print("❌ Failed to create complaint in database")
            msg.body("Sorry, something went wrong. Please try again later.")
            print("=" * 60)
            return str(resp)
        
        print(f"✅ Complaint created: #{complaint['resolve_token']}")
        
        # Send email to department
        print("📧 Sending email to department...")
        email_sent = send_department_email(complaint)
        if email_sent:
            print("✅ Email sent successfully")
        else:
            print("❌ Email failed to send")
        
        # Send confirmation to student
        confirmation_message = f"""✅ Complaint Received!

📋 ID: #{complaint['resolve_token']}
👤 Name: {student['student_name']}
🏢 Location: {student['hostel_name']}, Room {student['room_number']}
🏷️ Category: {classification['category']}
⚡ Priority: {classification['priority']}
📧 Assigned to: {classification['department_email'].split('@')[0].replace('_', ' ').title()} Department

You'll be notified once resolved! 🔔"""
        
        msg.body(confirmation_message)
        print("✅ WhatsApp confirmation sent to student")
        print("=" * 60)
        
        return str(resp)
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        
        # Send error message to user
        resp = MessagingResponse()
        msg = resp.message()
        msg.body("System error. Please contact hostel office.")
        return str(resp)


@app.route("/api/check-phone", methods=["GET"])
def check_phone():
    """Check if phone number is registered."""
    phone = request.args.get("phone")
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    # Add whatsapp: prefix and + if not present
    if not phone.startswith("whatsapp:"):
        # Add + if not present
        if not phone.startswith("+"):
            phone = f"+{phone}"
        phone = f"whatsapp:{phone}"
    
    student = check_student_exists(phone)
    return jsonify({"registered": student is not None})


@app.route("/api/register", methods=["POST"])
def api_register():
    """Register new student."""
    try:
        data = request.json
        
        print("=" * 60)
        print("📝 REGISTRATION REQUEST RECEIVED")
        print(f"Data: {data}")
        
        # Required fields (college_id is optional now, auto-generated if missing)
        required_fields = ["phone_number", "roll_number", "student_name", "hostel_name", "room_number"]
        for field in required_fields:
            if not data.get(field):
                print(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Auto-generate college_id if not provided
        if not data.get("college_id"):
            data["college_id"] = f"FIXXO{int(time.time())}"
            print(f"✅ Auto-generated college_id: {data['college_id']}")
        
        # Check if phone number already exists
        existing_student = check_student_exists(data["phone_number"])
        if existing_student:
            print(f"❌ Phone number already registered: {data['phone_number']}")
            return jsonify({"error": "Phone number already registered"}), 400
        
        # Check if college_id already exists
        try:
            existing_college = supabase.table("students").select("*").eq("college_id", data["college_id"]).execute()
            if existing_college.data and len(existing_college.data) > 0:
                # College ID exists, generate a new one
                data["college_id"] = f"FIXXO{int(time.time())}{random.randint(100, 999)}"
                print(f"⚠️ College ID conflict, using new ID: {data['college_id']}")
        except Exception as e:
            print(f"⚠️ Error checking college_id: {e}")
        
        # Register student
        print(f"✅ Registering student: {data['student_name']}")
        student = register_student(
            phone_number=data["phone_number"],
            college_id=data["college_id"],
            roll_number=data["roll_number"],
            student_name=data["student_name"],
            hostel_name=data["hostel_name"],
            room_number=data["room_number"],
            email=data.get("email")
        )
        
        if student:
            print(f"✅ Student registered successfully!")
            print("=" * 60)
            return jsonify({"success": True, "student": student}), 201
        else:
            print(f"❌ Registration failed - database error")
            print("=" * 60)
            return jsonify({"error": "Database error - registration failed"}), 500
            
    except Exception as e:
        print(f"❌ Registration exception: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return jsonify({"error": str(e)}), 500


def require_admin(f):
    """Decorator to require admin authentication."""
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """Admin login."""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        
        print("=" * 60)
        print("🔐 ADMIN LOGIN ATTEMPT")
        print(f"Username: {username}")
        print(f"Password length: {len(password) if password else 0}")
        
        if not username or not password:
            print("❌ Missing username or password")
            return jsonify({"error": "Username and password required"}), 400
        
        # Query admin from database
        try:
            response = supabase.table("admins").select("*").eq("username", username).eq("is_active", True).execute()
            
            print(f"Database query result: {response.data}")
            
            if not response.data or len(response.data) == 0:
                print(f"❌ Admin not found: {username}")
                return jsonify({"error": "Invalid credentials"}), 401
            
            admin = response.data[0]
            print(f"✅ Admin found: {admin['username']}")
            
            # Simple password check (plaintext for now - NOT SECURE, just for testing)
            if admin['password_hash'] != password:
                print(f"❌ Password mismatch")
                print(f"   Expected: {admin['password_hash']}")
                print(f"   Got: {password}")
                return jsonify({"error": "Invalid credentials"}), 401
            
            # Login successful
            print(f"✅ Login successful!")
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            
            # Update last login
            try:
                supabase.table("admins").update({
                    "last_login": datetime.utcnow().isoformat()
                }).eq("id", admin["id"]).execute()
            except Exception as e:
                print(f"⚠️ Could not update last_login: {e}")
            
            print("=" * 60)
            return jsonify({
                "success": True,
                "admin": {
                    "id": admin["id"],
                    "username": admin["username"],
                    "email": admin.get("email"),
                    "full_name": admin.get("full_name")
                }
            }), 200
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Database error"}), 500
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    """Admin logout."""
    session.clear()
    return jsonify({"success": True}), 200


@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    """Get dashboard statistics."""
    try:
        stats = get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/students", methods=["GET"])
@require_admin
def admin_get_students():
    """Get all students."""
    try:
        students = get_all_students()
        return jsonify(students), 200
    except Exception as e:
        print(f"❌ Error getting students: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/complaints", methods=["GET"])
@require_admin
def admin_get_complaints():
    """Get all complaints."""
    try:
        status = request.args.get("status")
        complaints = get_all_complaints(status=status)
        return jsonify(complaints), 200
    except Exception as e:
        print(f"❌ Error getting complaints: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/complaints/<complaint_id>", methods=["PUT"])
@require_admin
def admin_update_complaint(complaint_id):
    """Update complaint status."""
    try:
        data = request.json
        status = data.get("status")
        admin_notes = data.get("admin_notes")
        
        resolved_by = session.get("admin_username", "Admin")
        
        complaint = update_complaint_status(
            complaint_id=complaint_id,
            status=status,
            resolved_by=resolved_by,
            admin_notes=admin_notes
        )
        
        if complaint:
            # Send WhatsApp notification if resolved
            if status == "RESOLVED":
                send_whatsapp_notification(complaint)
            
            return jsonify({"success": True, "complaint": complaint}), 200
        else:
            return jsonify({"error": "Failed to update complaint"}), 500
            
    except Exception as e:
        print(f"❌ Error updating complaint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/resolve", methods=["GET"])
def resolve_complaint():
    """Resolve complaint via email link."""
    try:
        token = request.args.get("token")
        if not token:
            return "❌ Invalid resolution link", 400
        
        # Get complaint by token
        complaint = get_complaint_by_token(token)
        if not complaint:
            return "❌ Complaint not found", 404
        
        if complaint['status'] == 'RESOLVED':
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Already Resolved</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        text-align: center;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        max-width: 500px;
                    }}
                    .icon {{ font-size: 80px; margin-bottom: 20px; }}
                    h1 {{ color: #1f2937; margin-bottom: 20px; }}
                    p {{ color: #6b7280; font-size: 18px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✅</div>
                    <h1>Already Resolved</h1>
                    <p>This complaint was already marked as resolved.</p>
                    <p><strong>ID:</strong> #{complaint['resolve_token']}</p>
                </div>
            </body>
            </html>
            """
        
        # Update complaint status
        updated_complaint = update_complaint_status(
            complaint_id=complaint['id'],
            status='RESOLVED',
            resolved_by='Department'
        )
        
        # Send WhatsApp notification
        if updated_complaint:
            send_whatsapp_notification(updated_complaint)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complaint Resolved</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                }}
                .icon {{ font-size: 80px; margin-bottom: 20px; }}
                h1 {{ color: #1f2937; margin-bottom: 20px; }}
                p {{ color: #6b7280; font-size: 18px; margin-bottom: 10px; }}
                .success {{ color: #10b981; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🎉</div>
                <h1>Complaint Resolved!</h1>
                <p><strong>ID:</strong> #{complaint['resolve_token']}</p>
                <p><strong>Category:</strong> {complaint['category']}</p>
                <p class="success">✅ Student has been notified via WhatsApp</p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"❌ Resolution error: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)