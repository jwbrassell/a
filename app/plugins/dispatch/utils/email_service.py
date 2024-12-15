"""Email service for dispatch notifications."""

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_dispatch_email(transaction):
    """Send email notification for dispatch transaction.
    
    Args:
        transaction: DispatchTransaction instance
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Build email body
        rma_section = f'<tr><td><b>RMA Information</b></td><td>{transaction.rma_info}</td></tr>' if transaction.is_rma else ''
        bridge_section = f'<tr><td><b>Bridge Link</b></td><td><a href="{transaction.bridge_link}">{transaction.bridge_link}</a></td></tr>' if transaction.is_bridge else ''
        
        body = f'''
        <table border="1" cellpadding="5">
            <tr><td><b>Team</b></td><td>{transaction.team.name}</td></tr>
            <tr><td><b>Priority</b></td><td>{transaction.priority.name}</td></tr>
            <tr><td><b>Description</b></td><td>{transaction.description}</td></tr>
            <tr><td><b>Requestor</b></td><td>{transaction.created_by_name}</td></tr>
            {rma_section}
            {bridge_section}
        </table>
        '''

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = transaction.team.email
        msg['Subject'] = f'Dispatch Request - {transaction.team.name}'
        msg.attach(MIMEText(body, 'html'))

        # Send email
        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            
            server.send_message(msg)
            
        logger.info(f"Email sent successfully for dispatch request {transaction.id}")
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
