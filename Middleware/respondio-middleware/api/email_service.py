"""
Email service for ORBIT alerts using aiosmtplib.
"""

import aiosmtplib
from email.message import EmailMessage
import logging
from .config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending alert emails"""
    
    def __init__(self):
        self.host = settings.SMTP_SERVER
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.recipient = settings.ALERT_EMAIL_RECIPIENT
        self.enabled = bool(self.host and self.user and self.password)

    async def send_alert(self, subject: str, body: str) -> bool:
        """Send an alert email"""
        if not self.enabled:
            logger.warning("Email alerts disabled (missing SMTP configuration)")
            return False
            
        try:
            message = EmailMessage()
            message["From"] = self.user
            message["To"] = self.recipient or self.user # Fallback to sender
            message["Subject"] = f"🚨 ORBIT Alert: {subject}"
            message.set_content(body)
            
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=(self.port == 587),
                use_tls=(self.port == 465)
            )
            
            logger.info(f"Alert email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False

# Singleton instance
email_service = EmailService()
