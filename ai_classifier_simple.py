import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DEPARTMENT_EMAILS = {
    "PLUMBING": "plumbing@university.edu",
    "ELECTRICAL": "electrical@university.edu",
    "CLEANLINESS": "housekeeping@university.edu",
    "SECURITY": "security@university.edu",
    "WIFI": "it@university.edu",
    "FOOD": "mess@university.edu",
    "FURNITURE": "warden@university.edu",
    "OTHER": "admin@university.edu"
}


def classify_complaint(message_text, image_url=None):

    prompt = f"""
You are a hostel complaint classifier.

Extract structured information from this complaint:

MESSAGE: {message_text}

Return ONLY JSON:

{{
  "hostel_name": string or null,
  "room_number": string or null,
  "category": "PLUMBING" | "ELECTRICAL" | "CLEANLINESS" | "SECURITY" | "WIFI" | "FOOD" | "FURNITURE" | "OTHER",
  "priority": "LOW" | "MEDIUM" | "HIGH" | "URGENT",
  "summary": string
}}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Best free model
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured hostel complaint data."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        text = response.choices[0].message.content.strip()

        # Remove markdown formatting if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        category = result.get("category", "OTHER")

        result["department_email"] = DEPARTMENT_EMAILS.get(
            category,
            DEPARTMENT_EMAILS["OTHER"]
        )

        result["confidence"] = 96.0

        print("✅ Groq classifier working")

        return result

    except Exception as e:

        print("❌ Groq error:", e)

        return {
            "hostel_name": None,
            "room_number": None,
            "category": "OTHER",
            "priority": "MEDIUM",
            "summary": message_text[:100],
            "department_email": DEPARTMENT_EMAILS["OTHER"],
            "confidence": 0
        }


# Test
if __name__ == "__main__":

    test_message = "KP-7 hostel room 312 wifi not working urgent"

    result = classify_complaint(test_message)

    print(result)