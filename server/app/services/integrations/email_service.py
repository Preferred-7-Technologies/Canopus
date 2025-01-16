import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import imaplib
import email
from ...config import settings
from ...core.logging import setup_logging

logger = setup_logging()

class EmailService:
    def __init__(self):
        self.smtp_settings = {
            "hostname": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "username": settings.EMAIL_USERNAME,
            "password": settings.EMAIL_PASSWORD,
            "use_tls": True
        }
        self.imap_settings = {
            "server": settings.IMAP_SERVER,
            "username": settings.EMAIL_USERNAME,
            "password": settings.EMAIL_PASSWORD
        }

    async def send_email(self, recipient: str, subject: str, content: str) -> Dict[str, Any]:
        try:
            message = MIMEMultipart()
            message["From"] = self.smtp_settings["username"]
            message["To"] = recipient
            message["Subject"] = subject
            message.attach(MIMEText(content, "plain"))

            async with aiosmtplib.SMTP(**self.smtp_settings) as smtp:
                await smtp.send_message(message)

            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            raise

    async def read_emails(self, folder: str = "INBOX", limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with imaplib.IMAP4_SSL(self.imap_settings["server"]) as imap:
                imap.login(self.imap_settings["username"], self.imap_settings["password"])
                imap.select(folder)
                _, message_numbers = imap.search(None, "ALL")
                
                emails = []
                for num in message_numbers[0].split()[-limit:]:
                    _, msg = imap.fetch(num, "(RFC822)")
                    email_body = email.message_from_bytes(msg[0][1])
                    emails.append({
                        "subject": email_body["subject"],
                        "from": email_body["from"],
                        "date": email_body["date"],
                        "content": self._get_email_content(email_body)
                    })
                
                return emails
        except Exception as e:
            logger.error(f"Email reading failed: {str(e)}")
            raise

    def _get_email_content(self, email_message) -> str:
        if email_message.is_multipart():
            return self._get_email_content(email_message.get_payload(0))
        return email_message.get_payload()
