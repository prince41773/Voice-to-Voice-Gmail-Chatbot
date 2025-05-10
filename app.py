import sys
import os
import re
import pyttsx3
from flask import Flask, render_template, jsonify, request
from threading import Thread
import google.generativeai as genai

# Get the absolute path of the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(BASE_DIR, "utils")
my_name = "tirth"
sys.path.insert(0, UTILS_DIR)

from stt import listen
from tts import speak
from nlp import detect_intent, extract_email_details, extract_name_email
from gmail import authenticate_gmail, read_emails, create_email, send_email, get_email_address

genai.configure(api_key="AIzaSyBUcPB5kFcQYv9vLEB7CvLhGY3IMDlGfEo")

# model to generate email
model = genai.GenerativeModel('gemini-2.0-flash')

def gemini_generate_email(topic):
    response = model.generate_content(topic)
    email_content = response.text
    return email_content

def extract_subject_body(text, keyword):
    lines = text.split("\n")
    subject, body = None, None
    for i, line in enumerate(lines):
        if keyword in line:
            if i + 1 < len(lines):
                subject = lines[i + 1]
                body = "\n".join(lines[i + 2:])
            break
    return body

def get_next_string(text, keyword):
    index = text.find(keyword)
    if index == -1:
        return None
    start = index + len(keyword)
    end = text.find("\n", start)
    return text[start:end] if end != -1 else text[start:]

def format_email(email):
    email = email.lower()
    email = email.replace(" at the rate ", "@").replace(" at ", "@").replace(" dot ", ".")
    email = "".join(email.split())
    return email

def detect_email_reading_intent(user_input):
    match = re.search(r"read my top (\d+) emails", user_input, re.IGNORECASE)
    if match:
        return int(match.group(1))
    elif "read my emails" in user_input.lower():
        return 4
    return None

app = Flask(__name__)
service = authenticate_gmail()
session_data = {}
pending_email = {"recipient": None, "subject": None, "body": None}
current_stage = "INITIAL"
recipient_name = ""

@app.route("/")
def index():
    return render_template("index.html", pending_email=pending_email, emails=[])
pending_email = {
    "recipient": "",
    "subject": "",
    "body": ""
}

@app.route("/update-pending-email", methods=["POST"])
def update_pending_email():
    data = request.get_json()
    recipient = data.get("recipient")

    if recipient:
        pending_email["recipient"] = recipient
        return {"message": "Recipient updated successfully"}, 200
    else:
        return {"error": "Recipient missing"}, 400
    
@app.route("/voice-command", methods=["POST"])
def voice_command():
    global pending_email, current_stage, recipient_name

    user_input = request.json.get("text") or listen()
    user_input = user_input.strip()
    print(f"🗣️ User Input: {user_input}")

    intent = detect_intent(user_input)
    num_emails = detect_email_reading_intent(user_input)

    if user_input.lower() == "ayush":
        query = "from:Ayush"
        emails = get_email_address(service, query)
        print(emails)

    if intent == "READ" or num_emails:
        num_emails = num_emails or 4
        emails = read_emails(service, num_emails)
        if emails:
            Thread(target=speak, args=(f"Here are your top {num_emails} emails.",)).start()
            for email in emails:
                Thread(target=speak, args=(email,)).start()
            return jsonify({"response": f"Here are your top {num_emails} emails.", "emails": emails})
        else:
            Thread(target=speak, args=("No emails found.",)).start()
            return jsonify({"response": "No emails found.", "emails": []})

    if intent == "GENERATE":
        recipient_name, content = extract_email_details(user_input)
        if recipient_name and content:
            pending_email = {"recipient_name": recipient_name, "content": content, "subject": None, "body": None}
            Thread(target=speak, args=(f"Recipient name is {recipient_name}. Generating email now.",)).start()
            prompt = f"Write a short and professional email to {recipient_name} about: {content} behalf of {my_name}. Include only necessary details without placeholders."
            generated_email = gemini_generate_email(prompt)

            subject = get_next_string(generated_email, "Subject:")
            body = extract_subject_body(generated_email, "Subject:")

            pending_email["subject"] = subject
            pending_email["body"] = body

            Thread(target=speak, args=(f"Subject: {subject}. Email body generated.",)).start()

            query = f"from:{recipient_name}"
            matching_emails = list(get_email_address(service, query))

            if matching_emails:
                email_list = []
                for raw_email in matching_emails:
                    name, email = extract_name_email(raw_email)
                    email_list.append(f"{name} ({email})")
                session_data["email_list"] = matching_emails
                Thread(target=speak, args=("Multiple emails found. Please select by clicking or saying the email.",)).start()
                return jsonify({
                    "response": f"Multiple emails found for {recipient_name}.",
                    "pending_email": pending_email,
                    "emails": matching_emails
                })
            else:
                Thread(target=speak, args=("No matching email addresses found.",)).start()
                return jsonify({"response": "No matching email addresses found.", "pending_email": pending_email})

    if intent == "SELECT_EMAIL":
        match = re.search(r"\bselect\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", user_input)
        if match:
            selected_email = match.group(1).strip()
            print(f"Selected Email: {selected_email}")

            # Now, complete the email sending flow
            if pending_email.get("subject") and pending_email.get("body"):
                message = create_email(selected_email, pending_email["subject"], pending_email["body"])
                send_email(service, message)

                Thread(target=speak, args=(f"Email sent successfully to {selected_email}.",)).start()
                pending_email = {"recipient": None, "subject": None, "body": None}
                current_stage = "INITIAL"
                return jsonify({
                    "response": {
                        "stage1": f"Subject and Body prepared.",
                        "stage2": f"Recipient email selected: {selected_email}.",
                        "stage3": "Email sent successfully!"
                    },
                    "pending_email": pending_email
                })
            else:
                Thread(target=speak, args=("Email content not ready yet.",)).start()
                return jsonify({"response": "Email content not prepared yet. Please try again."})

    if current_stage == "INITIAL":
        if intent == "WRITE" or re.search(r"(write|compose)", user_input, re.I):
            pending_email = {"recipient": None, "subject": None, "body": None}
            current_stage = "RECIPIENT"
            Thread(target=speak, args=("Who do you want to email?",)).start()
            return jsonify({"response": "Please provide recipient email.", "pending_email": pending_email})

    elif current_stage == "RECIPIENT":
        if "@" in user_input or "at the rate" in user_input:
            formatted_email = format_email(user_input)
            pending_email["recipient"] = formatted_email
            current_stage = "SUBJECT"
            Thread(target=speak, args=("What is the subject?",)).start()
            return jsonify({"response": f"Recipient set: {formatted_email}. Now, provide subject.", "pending_email": pending_email})
        else:
            Thread(target=speak, args=("Please provide a valid email address.",)).start()
            return jsonify({"response": "Invalid email address. Try again.", "pending_email": pending_email})

    elif current_stage == "SUBJECT":
        pending_email["subject"] = user_input
        current_stage = "BODY"
        Thread(target=speak, args=("What is the message?",)).start()
        return jsonify({"response": f"Subject set: {user_input}. Now, provide message.", "pending_email": pending_email})

    elif current_stage == "BODY":
        pending_email["body"] = user_input
        email_preview = f"To: {pending_email['recipient']}\nSubject: {pending_email['subject']}\nMessage: {pending_email['body']}"
        current_stage = "SEND"
        Thread(target=speak, args=("Here is your email. Say 'Send' to send it.",)).start()
        return jsonify({"response": email_preview, "pending_email": pending_email})

    elif current_stage == "SEND":
        if intent == "SEND" or re.search(r"(send|confirm)", user_input, re.I):
            if all(pending_email.values()):
                email_data = create_email(pending_email["recipient"], pending_email["subject"], pending_email["body"])
                send_email(service, email_data)
                pending_email = {"recipient": None, "subject": None, "body": None}
                current_stage = "INITIAL"
                Thread(target=speak, args=("Email sent successfully!",)).start()
                return jsonify({"response": "Email sent successfully!", "pending_email": pending_email})

    Thread(target=speak, args=("I did not understand the command.",)).start()
    return jsonify({"response": "Command not recognized.", "pending_email": pending_email})

if __name__ == "__main__":
    app.run(debug=True)
