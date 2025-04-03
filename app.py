import sys
import os
import re
import pyttsx3
from flask import Flask, render_template, jsonify, request
from threading import Thread

# Get the absolute path of the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(BASE_DIR, "utils")

sys.path.insert(0, UTILS_DIR)

from stt import listen
from tts import speak
from nlp import detect_intent
from gmail import authenticate_gmail, read_emails, create_email, send_email

app = Flask(__name__)
service = authenticate_gmail()

pending_email = {"recipient": None, "subject": None, "body": None}
current_stage = "INITIAL"  # Track the email flow stages

def format_email(email):
    """Correcting common speech-to-text errors in email addresses."""
    email = email.lower()
    email = email.replace(" at the rate ", "@").replace(" at ", "@").replace(" dot ", ".")
    email = "".join(email.split())  # Removing unintended spaces
    return email

def detect_email_reading_intent(user_input):
    """Detect if the user wants to read emails & extract count."""
    match = re.search(r"read my top (\d+) emails", user_input, re.IGNORECASE)
    if match:
        return int(match.group(1))  # Extract number of emails
    elif "read my emails" in user_input.lower():
        return 4  # Default to 4 emails
    return None

@app.route("/")
def index():
    return render_template("index.html", pending_email=pending_email, emails=[])

@app.route("/voice-command", methods=["POST"])
def voice_command():
    global pending_email, current_stage

    user_input = request.json.get("text") or listen()
    user_input = user_input.strip()

    print(f"🗣️ User Input: {user_input}")
    intent = detect_intent(user_input)
    num_emails = detect_email_reading_intent(user_input)

    # Email Reading
    if intent == "READ" or num_emails:
        num_emails = num_emails or 4 
        emails = read_emails(service, num_emails)

        # print(f"📩 Emails to send to frontend: {emails}")  

        if emails:
            Thread(target=speak, args=(f"Here are your top {num_emails} emails.",)).start()
            for email in emails:
                Thread(target=speak, args=(email,)).start()

            return jsonify({
                "response": f"Here are your top {num_emails} emails.",
                "emails": emails
            })
        else:
            Thread(target=speak, args=("No emails found.",)).start()
            return jsonify({
                "response": "No emails found.",
                "emails": []
            })

    # Email Writing Flow
    if current_stage == "INITIAL":
        if intent == "WRITE" or re.search(r"(write|compose)", user_input, re.I):
            pending_email = {"recipient": None, "subject": None, "body": None}
            current_stage = "RECIPIENT"
            Thread(target=speak, args=("Who do you want to email?",)).start()
            return jsonify({
                "response": "Please provide recipient email.",
                "pending_email": pending_email
            })

    elif current_stage == "RECIPIENT":
        if "@" in user_input or "at the rate" in user_input:
            formatted_email = format_email(user_input)
            pending_email["recipient"] = formatted_email
            current_stage = "SUBJECT"
            Thread(target=speak, args=("What is the subject?",)).start()
            return jsonify({
                "response": f"Recipient set: {formatted_email}. Now, provide subject.",
                "pending_email": pending_email
            })
        else:
            Thread(target=speak, args=("Please provide a valid email address.",)).start()
            return jsonify({
                "response": "Invalid email address. Try again.",
                "pending_email": pending_email
            })

    elif current_stage == "SUBJECT":
        pending_email["subject"] = user_input
        current_stage = "BODY"
        Thread(target=speak, args=("What is the message?",)).start()
        return jsonify({
            "response": f"Subject set: {user_input}. Now, provide message.",
            "pending_email": pending_email
        })

    elif current_stage == "BODY":
        pending_email["body"] = user_input
        email_preview = f"To: {pending_email['recipient']}\nSubject: {pending_email['subject']}\nMessage: {pending_email['body']}"
        current_stage = "SEND"
        Thread(target=speak, args=("Here is your email. Say 'Send' to send it.",)).start()
        return jsonify({
            "response": email_preview,
            "pending_email": pending_email
        })

    elif current_stage == "SEND":
        if intent == "SEND" or re.search(r"(send|confirm)", user_input, re.I):
            if all(pending_email.values()):
                email_data = create_email(pending_email["recipient"], pending_email["subject"], pending_email["body"])
                send_email(service, email_data)
                pending_email = {"recipient": None, "subject": None, "body": None}
                current_stage = "INITIAL"
                Thread(target=speak, args=("Email sent successfully!",)).start()
                return jsonify({
                    "response": "Email sent successfully!",
                    "pending_email": pending_email
                })

    # Catch-all Response
    Thread(target=speak, args=("I did not understand the command.",)).start()
    return jsonify({
        "response": "Command not recognized.",
        "pending_email": pending_email
    })

if __name__ == "__main__":
    app.run(debug=True)
