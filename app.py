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
    update_complaint_status
)
from ai_classifier import classify_complaint
from email_sender import send_department_email, send_whatsapp_notification

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fixxo-super-secret-key-change-in-production-2026")

# CORS Configuration - UPDATED
CORS(app, 
     resources={r"/api/*": {"origins": "http://localhost:3000"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# ============================================
# WHATSAPP WEBHOOK (UPDATED!)
# ============================================

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    try:
        # Get message details
        incoming_msg = request.form.get("Body", "").strip()
        from_number = request.form.get("From", "")
        
        print(f"📱 Message from {from_number}: {incoming_msg}")
        
        # Check if student is registered
        student = check_student_exists(from_number)
        
        resp = MessagingResponse()
        msg = resp.message()
        
        if not student:
            # Student not registered - send registration link
            registration_link = f"{BASE_URL}/register?phone={from_number.replace('whatsapp:', '')}"
            
            msg.body(f"""👋 Welcome to Fixxo!

Please register first (one-time only):
🔗 {registration_link}

After registration, send your complaint again!""")
            
            print("⚠️ Student not registered, sending registration link")
            return str(resp)
        
        # Student is registered - process complaint
        print(f"✅ Student found: {student['student_name']}")
        
        # Classify complaint
        classification = classify_complaint(incoming_msg)
        
        # Prepare complaint data with student info
        complaint_data = {
            "student_id": student["id"],
            "student_phone": from_number,
            "student_name": student["student_name"],
            "hostel_name": student["hostel_name"],
            "room_number": student["room_number"],
            "category": classification["category"],
            "priority": classification["priority"],
            "raw_message": incoming_msg,
            "summary": classification["summary"],
            "department_email": classification["department_email"],
            "confidence": classification["confidence"],
            "status": "PENDING"
        }
        
        # Save to database
        saved_complaint = create_complaint(complaint_data)
        
        if saved_complaint:
            # Send email to department
            send_department_email(saved_complaint)
            
            # Send confirmation to student
            msg.body(f"""✅ Complaint Received!

📋 ID: #{saved_complaint['resolve_token']}
👤 Name: {student['student_name']}
🏢 Location: {student['hostel_name']}, Room {student['room_number']}
🏷️ Category: {classification['category']}
⚡ Priority: {classification['priority']}
📧 Assigned to: {classification['department_email'].split('@')[0].title()} Department

You'll be notified once resolved! 🔔""")
            
            print(f"✅ Complaint #{saved_complaint['resolve_token']} created")
        else:
            msg.body("❌ Sorry, something went wrong. Please try again later.")
        
        return str(resp)
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        resp = MessagingResponse()
        resp.message("❌ System error. Please contact hostel office.")
        return str(resp)

# ============================================
# REGISTRATION API (NEW!)
# ============================================

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

# ============================================
# ADMIN AUTH (NEW!)
# ============================================

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

def admin_required(f):
    """Decorator to require admin login."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ADMIN - STUDENTS API (NEW!)
# ============================================

@app.route("/api/admin/students", methods=["GET"])
@admin_required
def admin_get_students():
    """Get all students."""
    students = get_all_students()
    return jsonify(students), 200

@app.route("/api/admin/students", methods=["POST"])
@admin_required
def admin_add_student():
    """Manually add student."""
    return api_register()  # Reuse registration logic

@app.route("/api/admin/students/<student_id>", methods=["PUT"])
@admin_required
def admin_update_student(student_id):
    """Update student info."""
    try:
        data = request.json
        student = update_student(student_id, data)
        if student:
            return jsonify(student), 200
        else:
            return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/students/<student_id>", methods=["DELETE"])
@admin_required
def admin_delete_student(student_id):
    """Delete student."""
    if delete_student(student_id):
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Delete failed"}), 500

# ============================================
# ADMIN - COMPLAINTS API (NEW!)
# ============================================

@app.route("/api/admin/complaints", methods=["GET"])
@admin_required
def admin_get_complaints():
    """Get all complaints."""
    status = request.args.get("status")  # Optional filter
    complaints = get_all_complaints(status=status)
    return jsonify(complaints), 200

@app.route("/api/admin/complaints/<complaint_id>", methods=["PUT"])
@admin_required
def admin_update_complaint(complaint_id):
    """Update complaint (e.g., mark resolved)."""
    try:
        data = request.json
        # Implementation depends on what you want to update
        # For now, just return success
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/complaints/<complaint_id>/note", methods=["POST"])
@admin_required
def admin_add_note(complaint_id):
    """Add internal note to complaint."""
    try:
        data = request.json
        note = data.get("note")
        if not note:
            return jsonify({"error": "Note required"}), 400
        
        complaint = add_admin_note(complaint_id, note)
        if complaint:
            return jsonify(complaint), 200
        else:
            return jsonify({"error": "Complaint not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ADMIN - ANALYTICS (NEW!)
# ============================================

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_get_stats():
    """Get dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats), 200

# ============================================
# RESOLVE COMPLAINT (EXISTING - KEEP AS IS)
# ============================================

@app.route("/resolve", methods=["GET"])
def resolve():
    """Mark complaint as resolved (from email link)."""
    token = request.args.get("token")
    
    if not token:
        return "❌ Invalid resolve link", 400
    
    complaint = get_complaint_by_token(token)
    
    if not complaint:
        return "❌ Complaint not found", 404
    
    if complaint["status"] == "RESOLVED":
        return "✅ This complaint was already resolved", 200
    
    # Mark as resolved
    resolved_complaint = resolve_complaint(token, resolved_by="Department")
    
    if resolved_complaint:
        # Send WhatsApp notification to student
        send_whatsapp_notification(resolved_complaint)
        
        return f"""
        <html>
        <head><title>Complaint Resolved</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: green;">✅ Complaint Resolved!</h1>
            <p>Complaint ID: #{token}</p>
            <p>Student has been notified via WhatsApp.</p>
            <p><a href="{BASE_URL}/api/admin/complaints">View all complaints</a></p>
        </body>
        </html>
        """, 200
    else:
        return "❌ Failed to resolve complaint", 500

# ============================================
# HEALTH CHECK (EXISTING)
# ============================================

@app.route("/", methods=["GET"])
def home():
    return "🏠 Fixxo API is running!", 200

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
