import os
import uuid
import secrets
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def save_complaint(student_phone, raw_message, ai_result):
    """
    Save a new complaint to the database.
    
    Args:
        student_phone: WhatsApp number of student
        raw_message: Original message text
        ai_result: Dictionary from ML classifier
    
    Returns:
        The saved complaint record with ID
    """
    try:
        # Generate a unique resolve token for email link
        resolve_token = secrets.token_urlsafe(32)
        
        # Build the complaint record
        complaint = {
            "student_phone": student_phone,
            "hostel_name": ai_result.get("hostel_name"),
            "room_number": ai_result.get("room_number"),
            "category": ai_result.get("category", "OTHER"),
            "priority": ai_result.get("priority", "MEDIUM"),
            "raw_message": raw_message,
            "summary": ai_result.get("summary", raw_message[:100]),
            "department_email": ai_result.get("department_email"),
            "confidence": ai_result.get("confidence", 0),
            "status": "PENDING",
            "resolve_token": resolve_token
        }
        
        # Insert into Supabase
        response = supabase.table("complaints").insert(complaint).execute()
        
        saved_record = response.data[0]
        complaint_id = saved_record["id"]
        
        print(f"✅ Complaint saved to database!")
        print(f"   ID: {complaint_id}")
        print(f"   Status: PENDING")
        
        return saved_record
        
    except Exception as e:
        print(f"❌ Database error while saving: {e}")
        return None


def resolve_complaint(resolve_token, resolution_note=None):
    """
    Mark a complaint as resolved using the resolve token.
    
    Args:
        resolve_token: The unique token from the email link
        resolution_note: Optional note from department
    
    Returns:
        The updated complaint record
    """
    try:
        from datetime import datetime, timezone
        
        # Update the complaint status
        update_data = {
            "status": "RESOLVED",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolution_note": resolution_note or "Issue has been resolved."
        }
        
        response = (
            supabase.table("complaints")
            .update(update_data)
            .eq("resolve_token", resolve_token)
            .execute()
        )
        
        if response.data:
            record = response.data[0]
            print(f"✅ Complaint {record['id']} marked as RESOLVED!")
            return record
        else:
            print(f"❌ No complaint found with that token")
            return None
            
    except Exception as e:
        print(f"❌ Database error while resolving: {e}")
        return None


def get_complaint_by_token(resolve_token):
    """Get a complaint record by its resolve token."""
    try:
        response = (
            supabase.table("complaints")
            .select("*")
            .eq("resolve_token", resolve_token)
            .execute()
        )
        
        if response.data:
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


def get_all_complaints():
    """Get all complaints ordered by newest first."""
    try:
        response = (
            supabase.table("complaints")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []


# Test function
if __name__ == "__main__":
    print("🧪 Testing database connection...")
    complaints = get_all_complaints()
    print(f"✅ Connected! Total complaints in DB: {len(complaints)}")