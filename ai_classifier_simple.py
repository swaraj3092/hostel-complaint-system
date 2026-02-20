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
    "PLUMBING": ["tap", "water", "leak", "pipe", "flush", "toilet", "bathroom", "shower", "drain", "plumb"],
    "ELECTRICAL": ["light", "electricity", "power", "bulb", "switch", "fan", "ac", "socket"],
    "CLEANLINESS": ["clean", "dirty", "garbage", "trash", "smell","hygiene", "pest", "insect", "rodent"],
    "SECURITY": ["security", "lock", "key", "door", "stranger", "theft", "safety", "cctv", "guard", "intruder", "break-in"],
    "WIFI": ["wifi", "internet", "network", "connection", "slow", "disconnect", "signal", "router", "bandwidth", "latency", "data", "speed", "access", "coverage", "outage", "login", "password", "portal"],
    "FOOD": ["food", "mess", "meal", "quality", "taste", "hygiene", "menu", "cooking", "vegetarian", "non-vegetarian", "snack", "breakfast", "lunch", "dinner", "bottle", "canteen"],
    "FURNITURE": ["bed", "chair", "table", "furniture", "sofa", "desk", "cupboard", "drawer", "shelf", "couch", "furnishings", "fixture", "mattress", "wardrobe", "fitting", "cabinet", "stool", "bench", "dining", "furnishing", "upholstery"]
}

def extract_hostel_name(text):
    """
    Extract hostel name from common formats like:
    KP-7, KP7, Block A, C Block, Kaveri Hostel, etc.
    """

    text_lower = text.lower()

    patterns = [

        # KP-7, KP7, kp 7
        r"\b(kp[\s\-]?\d+)\b",

        # Block A, block c
        r"\b(block[\s\-]?[a-z])\b",

        # C Block, A Block
        r"\b([a-z][\s\-]?block)\b",

        # Kaveri Hostel, Ganga Hostel
        r"\b([a-z]+\s+hostel)\b",

        # Hostel KP-7, hostel kp7
        r"\bhostel[\s\-]?([a-z0-9\-]+)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            hostel = match.group(1).upper().replace(" ", "")
            return hostel

    return None

def extract_room_number(text):
    """
    Extract room number from formats like:
    room 312
    rm 101
    room no 204
    #312
    312 (fallback)
    """

    text_lower = text.lower()

    patterns = [

        # room 312
        r"\broom[\s\-]?(?:no[\s\-]?)?(\d{2,4})\b",

        # rm 312
        r"\brm[\s\-]?(\d{2,4})\b",

        # #312
        r"#(\d{2,4})",

        # fallback: standalone 3-4 digit number
        r"\b(\d{3,4})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1)

    return None

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