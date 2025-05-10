import os
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyttsx3

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]

def authenticate_gmail():
    """Authenticate and return the Gmail API service."""
    creds = None
    token_path = "token.json"
    credentials_path = r"D:\contribution\voice-email-chatbot-fin-copy\voice-email-chatbot\credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def create_email(to, subject, body):
    """Creates a properly formatted email message."""
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))
    return message

def send_email(service, message):
    """Encodes and sends the email."""
    try:
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode() 
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return "✅ Email sent successfully!"
    except Exception as e:
        return f"❌ Error sending email: {e}"

def read_emails(service, limit=5):
    """Fetches and returns the top unread emails formatted properly."""
    try:
        results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
        messages = results.get("messages", [])
        # print(f"🔍 Fetched {len(messages)} unread emails")  

        if not messages:
            return "No unread emails."

        emails = []
        for msg in messages[:limit]:  # Limiting the number of emails to fetch
            msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()

            subject = next((header["value"] for header in msg_data["payload"]["headers"] if header["name"] == "Subject"), "No Subject")
            sender = next((header["value"] for header in msg_data["payload"]["headers"] if header["name"] == "From"), "Unknown Sender")
            snippet = msg_data.get("snippet", "No Content")

            # Formatting fetched email properly
            email_content = f"📩 From: {sender}\n📌 Subject: {subject}\n📝 {snippet}"
            emails.append(email_content)
        # print(emails)
        return emails
    except Exception as e:
        return [f"❌ Error Fetching Emails: {e}"]

def delete_email(service, email_id):
    """Deletes an email by its ID."""
    try:
        service.users().messages().delete(userId="me", id=email_id).execute()
        return "✅ Email deleted successfully!"
    except Exception as e:
        return f"❌ Error deleting email: {e}"

def read_emails_aloud(emails):
    """Reads emails aloud using text-to-speech."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 200)

    for email in emails:
        # print(email)  
        engine.say(email)

    engine.runAndWait()

def get_email_address(service, query):
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    email_addresses = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']
        for header in headers:
            if header['name'] in ['From', 'To']:
                email_addresses.append(header['value'])

    return set(email_addresses)
