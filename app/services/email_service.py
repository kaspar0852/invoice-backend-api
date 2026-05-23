import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings


class EmailDeliveryError(Exception):
    pass


class EmailService:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        from_name: str | None = None,
    ) -> None:
        self.host = host if host is not None else settings.SMTP_HOST
        self.port = port if port is not None else settings.SMTP_PORT
        self.username = username if username is not None else settings.SMTP_USERNAME
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.from_name = from_name if from_name is not None else settings.SMTP_FROM_NAME

    def send(self, recipient_email: str, subject: str, body: str) -> None:
        if not all([self.host, self.port, self.username, self.password, self.from_name]):
            raise EmailDeliveryError("SMTP configuration is incomplete")

        message = EmailMessage()
        message["From"] = formataddr((self.from_name, self.username))
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.username, self.password)
                smtp.send_message(message)
        except Exception as exc:
            raise EmailDeliveryError(str(exc) or "Email delivery failed") from exc
