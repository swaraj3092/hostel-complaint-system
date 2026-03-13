import os
from resend import Resend
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

resend = Resend(api_key=RESEND_API_KEY)


def send_department_email(complaint):
    """Send email notification to department with complaint details."""
    try:
        print("=" * 60)
        print("📧 EMAIL FUNCTION STARTED")
        print(f"   To: {complaint.get('department_email')}")
        
        # Create resolve link using BASE_URL from environment
        resolve_link = f"{BASE_URL}/resolve?token={complaint['resolve_token']}"
        
        # Priority color coding
        priority_colors = {
            "URGENT": "#dc2626",
            "HIGH": "#ea580c",
            "MEDIUM": "#f59e0b",
            "LOW": "#3b82f6"
        }
        priority_color = priority_colors.get(complaint.get('priority', 'MEDIUM'), "#f59e0b")
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ padding: 30px; }}
                .priority-badge {{ display: inline-block; background-color: {priority_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; }}
                .info-row {{ margin: 15px 0; padding: 12px; background-color: #f9fafb; border-left: 4px solid #667eea; border-radius: 4px; }}
                .info-label {{ font-weight: bold; color: #4b5563; margin-bottom: 5px; }}
                .info-value {{ color: #1f2937; font-size: 16px; }}
                .message-box {{ background-color: #eff6ff; border: 2px solid #3b82f6; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .resolve-button {{ display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin: 20px 0; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3); }}
                .resolve-button:hover {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); }}
                .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 New Complaint Received</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Hostel Complaint Management System</p>
                </div>
                
                <div class="content">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span class="priority-badge">⚡ {complaint.get('priority', 'MEDIUM')} PRIORITY</span>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">📋 Complaint ID:</div>
                        <div class="info-value">#{complaint['resolve_token']}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">👤 Student Name:</div>
                        <div class="info-value">{complaint.get('student_name', 'N/A')}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">📞 Contact:</div>
                        <div class="info-value">{complaint.get('student_phone', 'N/A')}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">🏢 Location:</div>
                        <div class="info-value">{complaint.get('hostel_name', 'N/A')}, Room {complaint.get('room_number', 'N/A')}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">🏷️ Category:</div>
                        <div class="info-value">{complaint.get('category', 'OTHER')}</div>
                    </div>
                    
                    <div class="message-box">
                        <div class="info-label">💬 Issue Description:</div>
                        <div class="info-value" style="margin-top: 10px;">{complaint.get('raw_message', 'No description provided')}</div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{resolve_link}" class="resolve-button">
                            ✅ Mark as Resolved
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; text-align: center;">
                        Click the button above once the issue has been fixed. The student will be notified automatically.
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 5px 0;">Powered by <strong>Fixxo</strong></p>
                    <p style="margin: 5px 0;">Open Source Hostel Management System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email via Resend
        params = {
            "from": "Fixxo <onboarding@resend.dev>",
            "to": [complaint['department_email']],
            "subject": f"[{complaint.get('priority', 'MEDIUM')}] {complaint.get('category', 'NEW')} Issue - {complaint.get('hostel_name', 'Hostel')} Room {complaint.get('room_number', 'N/A')}",
            "html": html_content
        }
        
        email = resend.emails.send(params)
        
        print("✅ EMAIL SENT SUCCESSFULLY")
        print(f"   Email ID: {email.get('id', 'Unknown')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ EMAIL ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False


def send_whatsapp_notification(complaint):
    """Send WhatsApp notification to student when complaint is resolved."""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        client = Client(account_sid, auth_token)
        
        message_body = f"""✅ Great news!

Your complaint #{complaint['resolve_token']} has been RESOLVED!

📋 Issue: {complaint['category']}
🏢 Location: {complaint.get('hostel_name', 'N/A')}, Room {complaint.get('room_number', 'N/A')}
✅ Resolved by: {complaint.get('resolved_by', 'Department')}

Thank you for reporting! 🎉"""
        
        message = client.messages.create(
            from_=twilio_number,
            body=message_body,
            to=complaint['student_phone']
        )
        
        print(f"✅ WhatsApp notification sent: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send WhatsApp notification: {e}")
        return False