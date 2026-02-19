import os
import resend
from dotenv import load_dotenv

load_dotenv()

# Resend API key
resend.api_key = os.getenv("RESEND_API_KEY")

GMAIL_USER = os.getenv("GMAIL_USER")


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

    print("=" * 60)
    print("📧 EMAIL FUNCTION STARTED")
    print(f"To: {complaint.get('department_email')}")
    print("=" * 60)

    try:

        resolve_link = f"{resolve_base_url}/resolve?token={complaint['resolve_token']}"

        priority = complaint.get("priority", "MEDIUM")
        category = complaint.get("category", "OTHER")

        priority_color = PRIORITY_COLORS.get(priority, "#eab308")
        category_icon = CATEGORY_ICONS.get(category, "📋")

        complaint_id = str(complaint["id"])[:8].upper()

        # FULL ORIGINAL HTML (UNCHANGED)
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
            <div style="background: white; padding: 25px;">
                
                <h2 style="color: #1e293b;">
                    {category_icon} {category} Issue — #{complaint_id}
                </h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td><strong>Student Phone</strong></td>
                        <td>{complaint.get('student_phone')}</td>
                    </tr>

                    <tr>
                        <td><strong>Hostel</strong></td>
                        <td>{complaint.get('hostel_name', 'Not specified')}</td>
                    </tr>

                    <tr>
                        <td><strong>Room</strong></td>
                        <td>{complaint.get('room_number', 'Not specified')}</td>
                    </tr>

                    <tr>
                        <td><strong>Category</strong></td>
                        <td>{category}</td>
                    </tr>

                    <tr>
                        <td><strong>Priority</strong></td>
                        <td>{priority}</td>
                    </tr>

                    <tr>
                        <td><strong>Confidence</strong></td>
                        <td>{complaint.get('confidence', 0)}%</td>
                    </tr>

                </table>

                <br>

                <div style="background: #f8fafc; padding: 15px; border-radius: 8px;">
                    <strong>Student Message:</strong>
                    <p>{complaint.get('raw_message')}</p>
                </div>

                <br>

                <div style="text-align: center;">
                    <a href="{resolve_link}" 
                    style="background: #22c55e; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px;">
                    ✅ Mark as Resolved
                    </a>
                </div>

            </div>

            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 15px; text-align: center;">
                <p style="font-size: 13px;">
                Automated email from Hostel Complaint System
                </p>
            </div>

        </body>
        </html>
        """

        print("📧 Sending email via Resend API...")

        params = {
            "from": "Hostel Complaint System <onboarding@resend.dev>",
            "to": [complaint.get("department_email")],
            "subject": f"[{priority}] {category_icon} New Complaint #{complaint_id}",
            "html": html_content,
        }

        resend.Emails.send(params)

        print("=" * 60)
        print("✅ EMAIL SENT SUCCESSFULLY via Resend")
        print("=" * 60)

        return True

    except Exception as e:

        print("=" * 60)
        print(f"❌ EMAIL ERROR: {e}")
        print("=" * 60)

        return False
