"""Simple email service for sending notifications."""

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_notification_email(subject: str, body: str, recipients: list):
    """Send a notification email using local SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = 'donotreply@localhost'
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Log the email instead of sending in development
        logger.info(f"""
        =====================================
        Email Notification (Development Mode)
        =====================================
        To: {msg['To']}
        Subject: {subject}
        
        {body}
        =====================================
        """)

        # In production, you would uncomment this to actually send emails
        # with smtplib.SMTP('localhost') as server:
        #     server.send_message(msg)

    except Exception as e:
        logger.error(f"Error sending notification email: {e}")
