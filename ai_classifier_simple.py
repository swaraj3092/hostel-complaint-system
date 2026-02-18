import re

DEPARTMENT_EMAILS = {
    "PLUMBING": "swarajbehera923@gmail.com",
    "ELECTRICAL": "swarajbehera923@gmail.com",
    "CLEANLINESS": "swarajbehera923@gmail.com",
    "SECURITY": "swarajbehera923@gmail.com",
    "WIFI": "swarajbehera923@gmail.com",
    "FOOD": "swarajbehera923@gmail.com",
    "FURNITURE": "swarajbehera923@gmail.com",
    "OTHER": "swarajbehera923@gmail.com"
}

CATEGORY_KEYWORDS = {
    "PLUMBING": ["tap", "water", "leak", "pipe", "flush", "toilet", "bathroom", "shower", "drain"],
    "ELECTRICAL": ["light", "electricity", "power", "bulb", "switch", "fan", "ac", "socket"],
    "CLEANLINESS": ["clean", "dirty", "garbage", "trash", "smell"],
    "SECURITY": ["security", "lock", "key", "door", "stranger", "theft"],
    "WIFI": ["wifi", "internet", "network", "connection"],
    "FOOD": ["food", "mess", "meal", "quality"],
    "FURNITURE": ["bed", "chair", "table", "furniture"]
}

def extract_hostel_name(text):
    patterns = [r"(block\s+[a-z])", r"([a-z]+\s+hostel)"]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m: return m.group(1).title()
    return None

def extract_room_number(text):
    m = re.search(r"\b(\d{3,4})\b", text)
    return m.group(1) if m else None

def classify_category(text):
    t = text.lower()
    scores = {c: sum(1 for k in kws if k in t) for c, kws in CATEGORY_KEYWORDS.items()}
    return max(scores, key=scores.get) if any(scores.values()) else "OTHER"

def classify_priority(text):
    t = text.lower()
    if any(k in t for k in ["urgent", "emergency"]): return "URGENT"
    if any(k in t for k in ["not working", "broken"]): return "HIGH"
    return "MEDIUM"

def classify_complaint(message_text, image_url=None):
    return {
        "hostel_name": extract_hostel_name(message_text),
        "room_number": extract_room_number(message_text),
        "category": classify_category(message_text),
        "priority": classify_priority(message_text),
        "summary": message_text[:100],
        "department_email": DEPARTMENT_EMAILS.get(classify_category(message_text), DEPARTMENT_EMAILS["OTHER"]),
        "confidence": 85.0
    }