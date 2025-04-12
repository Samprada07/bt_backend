from email.message import EmailMessage
import aiosmtplib

EMAIL_SENDER = "samprada2058@gmail.com"
EMAIL_PASSWORD = "bjjexxnkksjdjhec"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

async def send_reset_email(to_email: str, reset_link: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = "Reset Your Password"
    msg.set_content(f"Click the link to reset your password: {reset_link}")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_SERVER,
        port=SMTP_PORT,
        start_tls=True,
        username=EMAIL_SENDER,
        password=EMAIL_PASSWORD,
    )
