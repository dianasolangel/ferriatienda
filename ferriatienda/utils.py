import smtplib # to send e-mails using smtp protocol 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv


# Load email configuration from environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def send_conversation_email(recipient_email: str, subject: str, messages: list) -> bool:
    """Send the conversation summary by email."""
    # We build up the email content
    html = "<h2>Resumen de la conversación</h2><ul>"
    for msg in messages:
        role = "Cliente" if msg["role"] == "user" else "Experto"
        html += f"<li><strong>{role}:</strong> {msg['content']}</li>"
    html += "</ul>"
    #creation of the email message
    msg = MIMEMultipart() # allows to combine different parts in the email
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Error al enviar el correo:", e)
        return False