"""
Email service for ORBIT alerts using Gmail API & aiosmtplib.
"""

import base64
from email.message import EmailMessage
from email.mime.text import MIMEText
import logging
import httpx
from typing import List, Optional
from .config import settings
from .config_manager import config_manager

logger = logging.getLogger(__name__)

OFFICIAL_RECIPIENTS = [
    "lmvega@maxillc.com",
    "mxmramirez@maxillc.com",
    "mxacbetanzos@maxillc.com",
    "elvega@maxillc.com",
    "gohernandez@maxillc.com",
    "mxgabad@maxillc.com",
    "mxjhurtado@maxillc.com",
    "jaclemente@maxillc.com"
]

class EmailService:
    """Service for sending alert emails via Gmail API or SMTP"""
    
    def __init__(self):
        self.host = settings.SMTP_SERVER
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.recipient = settings.ALERT_EMAIL_RECIPIENT
        self.enabled = bool(self.host and self.user and self.password)

    async def send_gmail_notification(
        self,
        subject: str,
        body_text: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """Send notification email via Gmail API using Google Service Account"""
        from .google_chat_service import google_chat_service
        
        target_recipients = recipients or OFFICIAL_RECIPIENTS
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("⚠️ Cannot send Gmail notification: Service Account JSON missing")
            return False
            
        try:
            creds = await google_chat_service._get_credentials(sa_b64)
            if not creds:
                logger.error("❌ Failed to obtain SA credentials for Gmail API")
                return False
                
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            
            # Construct MIME message
            msg = MIMEText(body_text, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['To'] = ", ".join(target_recipients)
            msg['From'] = "maxibot-sa@maxibot-472423.iam.gserviceaccount.com"
            
            raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            payload = {"raw": raw_b64}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    logger.info(f"📧 Gmail notification sent successfully to {len(target_recipients)} recipients for subject: '{subject}'")
                    return True
                else:
                    logger.error(f"❌ Gmail API returned status {res.status_code}: {res.text}")
                    return False
                    
        except Exception as err:
            logger.error(f"💥 Failed to send Gmail notification: {err}")
            return False

    async def send_alert(self, subject: str, body: str) -> bool:
        """Send an alert email using SMTP fallback"""
        if not self.enabled:
            logger.warning("Email alerts disabled (missing SMTP configuration)")
            return False
            
        try:
            message = EmailMessage()
            message["From"] = self.user
            message["To"] = self.recipient or self.user
            message["Subject"] = f"🚨 ORBIT Alert: {subject}"
            message.set_content(body)
            
            import aiosmtplib
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
