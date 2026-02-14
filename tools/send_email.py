import os
import smtplib
from email.message import EmailMessage

schema = {
    "name": "send_email",
    "description": (
        "Send an email from the operator's account. "
        "Always show the full draft (to, subject, body) to the user and get explicit confirmation before calling this tool."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "body": {
                "type": "string",
                "description": "Plain text email body"
            },
            "cc": {
                "type": "string",
                "description": "CC email address (optional)"
            },
        },
        "required": ["to", "subject", "body"]
    }
}


def execute(to: str, subject: str, body: str, cc: str = "") -> str:
    address = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_APP_PASSWORD")
    smtp_host = os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))

    if not address or not password:
        return "Error: EMAIL_ADDRESS and EMAIL_APP_PASSWORD must be set in .env"

    print(f"\n{'='*50}")
    print(f"  TO:      {to}")
    if cc:
        print(f"  CC:      {cc}")
    print(f"  SUBJECT: {subject}")
    print(f"  BODY:\n{body}")
    print(f"{'='*50}")
    confirm = input("Send this email? [y/N]: ").strip().lower()
    if confirm != "y":
        return "Email cancelled by user."

    msg = EmailMessage()
    msg["From"] = address
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(address, password)
            server.send_message(msg)
        return f"Email sent to {to}" + (f" (cc: {cc})" if cc else "")
    except Exception as e:
        return f"Failed to send email: {e}"
