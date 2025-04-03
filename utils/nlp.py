import re

def detect_intent(user_input):
    user_input = user_input.lower().strip()

    # Patterns for intent detection
    if re.search(r"\b(read|show|fetch|get)\s+(my\s+)?(emails|inbox|messages)\b", user_input):
        return "READ"
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
