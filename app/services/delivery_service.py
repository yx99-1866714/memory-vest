import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

class DeliveryService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_pass = settings.smtp_pass
        self.sender_email = settings.sender_email

    def send_report(self, to_email: str, subject: str, report_body: str) -> bool:
        """
        Sends the daily report via SMTP.
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(report_body, 'plain'))
        
        try:
            if self.smtp_port == 465:
                # SSL connection
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_pass:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
            else:
                # TLS connection (Port 587) or unencrypted (Port 1025)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_port == 587 or (self.smtp_user and self.smtp_pass):
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        
                    if self.smtp_user and self.smtp_pass:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
                    
            print(f"Report successfully sent to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
