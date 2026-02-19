import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Priority colors for email styling
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
    Send a formatted email to the department with complaint details
    and a one-click resolve button.
    
    Args:
        complaint: The saved complaint record from database
        resolve_base_url: Base URL of your server
    """
    
    print("=" * 60)
    print("📧 EMAIL FUNCTION STARTED")
    print(f"   To: {complaint.get('department_email')}")
    print(f"   Gmail User: {GMAIL_USER}")
    print(f"   Password Set: {bool(GMAIL_APP_PASSWORD)}")
    print("=" * 60)
    
    try:
        # Build the resolve link
        resolve_link = f"{resolve_base_url}/resolve?token={complaint['resolve_token']}"
        print(f"📧 Resolve link: {resolve_link}")
        
        # Get styling
        priority = complaint.get("priority", "MEDIUM")
        category = complaint.get("category", "OTHER")
        priority_color = PRIORITY_COLORS.get(priority, "#eab308")
        category_icon = CATEGORY_ICONS.get(category, "📋")
        
        # Short complaint ID for display
        complaint_id = str(complaint["id"])[:8].upper()
        
        print(f"📧 Building HTML email for complaint #{complaint_id}")
        
        # Build HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            
            <!-- Header -->
            <div style="background: #1e293b; color: white; padding: 25px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 22px;">🏠 Hostel Complaint System</h1>
                <p style="margin: 5px 0 0 0; color: #94a3b8;">New complaint assigned to your department</p>
            </div>
            
            <!-- Priority Banner -->
            <div style="background: {priority_color}; color: white; padding: 12px; text-align: center;">
                <strong>⚡ PRIORITY: {priority}</strong>
            </div>
            
            <!-- Complaint Details -->
            <div style="background: white; padding: 25px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
                
                <h2 style="color: #1e293b; margin-top: 0;">
                    {category_icon} {category} Issue — #{complaint_id}
                </h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b; width: 140px;"><strong>Student Phone</strong></td>
                        <td style="padding: 10px 5px; color: #1e293b;">{complaint.get('student_phone', 'Unknown')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b;"><strong>Hostel / Block</strong></td>
                        <td style="padding: 10px 5px; color: #1e293b;">{complaint.get('hostel_name') or 'Not specified'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b;"><strong>Room Number</strong></td>
                        <td style="padding: 10px 5px; color: #1e293b;">{complaint.get('room_number') or 'Not specified'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b;"><strong>Category</strong></td>
                        <td style="padding: 10px 5px; color: #1e293b;">{category}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b;"><strong>Priority</strong></td>
                        <td style="padding: 10px 5px;">
                            <span style="background: {priority_color}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 13px;">
                                {priority}
                            </span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 5px; color: #64748b;"><strong>ML Confidence</strong></td>
                        <td style="padding: 10px 5px; color: #1e293b;">{complaint.get('confidence', 0)}%</td>
                    </tr>
                </table>
                
                <!-- Complaint Message -->
                <div style="margin-top: 20px; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <strong style="color: #64748b;">Student's Message:</strong>
                    <p style="margin: 8px 0 0 0; color: #1e293b; line-height: 1.6;">
                        "{complaint.get('raw_message', '')}"
                    </p>
                </div>
                
                <!-- Resolve Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #64748b; margin-bottom: 15px;">
                        Once you have resolved this issue, click the button below:
                    </p>
                    <a href="{resolve_link}" 
                       style="background: #22c55e; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-size: 16px;
                              font-weight: bold; display: inline-block;">
                        ✅ Mark as Resolved
                    </a>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e2e8f0;">
                <p style="margin: 0; color: #94a3b8; font-size: 13px;">
                    This is an automated message from the Hostel Complaint Management System.<br>
                    Do not reply to this email. Use the button above to mark as resolved.
                </p>
            </div>
            
        </body>
        </html>
        """
        
        print("📧 Creating email message object...")
        
        # Set up the email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{priority}] {category_icon} New Hostel Complaint #{complaint_id} — {category}"
        msg["From"] = GMAIL_USER
        msg["To"] = complaint.get("department_email")
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))
        
        print("📧 Connecting to Gmail SMTP server (smtp.gmail.com:465)...")
        
        # Send via Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(
            GMAIL_USER,
            complaint.get("department_email"),
            msg.as_string()
        )
        server.quit()

        
        print("=" * 60)
        print(f"✅ EMAIL SENT SUCCESSFULLY to {complaint.get('department_email')}")
        print("=" * 60)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("=" * 60)
        print(f"❌ GMAIL LOGIN FAILED!")
        print(f"   Error: {e}")
        print(f"   Check your GMAIL_USER and GMAIL_APP_PASSWORD in Render")
        print("=" * 60)
        return False
        
    except smtplib.SMTPException as e:
        print("=" * 60)
        print(f"❌ SMTP ERROR!")
        print(f"   Error: {e}")
        print("=" * 60)
        return False
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ EMAIL ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False