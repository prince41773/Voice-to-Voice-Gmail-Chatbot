import re

def detect_intent(user_input):
    user_input = user_input.lower().strip()

    # patterns for intent detection
    if re.search(r"\bsend\s+an\s+email\s+to\b", user_input):
        return "GENERATE"
    elif re.search(r"\b(read|show|fetch|get)\s+(my\s+)?(emails|inbox|messages)\b", user_input):
        return "READ"
    elif re.search(r"\b(select|choose|pick)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d+)\b", user_input):
        return "SELECT_EMAIL"
    elif re.search(r"\b(write|compose|create|draft|send|make)\s+(an\s+)?email\b", user_input):
        return "WRITE"
    elif re.search(r"\b(send|dispatch|deliver|finalize)\s+(the\s+)?email\b", user_input):
        return "SEND"
    elif re.search(r"\b(read|show|fetch|get)\s+(my\s+)?(unread|new)\s+(emails|messages)\b", user_input):
        return "READ_UNREAD"
    elif re.search(r"\bsearch\s+email\s+with\s+word\s+(\w+)", user_input):
        match = re.search(r"\bsearch\s+email\s+with\s+word\s+(\w+)", user_input)
        return "SEARCH", match.group(1)

    return "UNKNOWN"

def extract_email_details(user_input):
    pattern = r"send an email to (.+?) (about|saying) (.+)"
    match = re.search(pattern, user_input.lower())
    if match:
        recipient_name = match.group(1).strip()
        content = match.group(3).strip()
        return recipient_name, content
    return None, None

def extract_number_from_input(user_input):

    number_words = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
        "tenth": 10
    }
    
    # First try to match number words
    for word, num in number_words.items():
        if re.search(rf"\b{word}\b", user_input, re.I):
            return num
    
    # If no word found, fallback to digits
    match = re.search(r"\b(\d+)\b", user_input)
    return int(match.group(1)) if match else None

def extract_name_email(text):
    match = re.match(r'(.*)<(.*)>', text)
    if match:
        name = match.group(1).strip().strip('"')
        email = match.group(2).strip()
        return name, email
    else:
        return text.strip(), text.strip() 
