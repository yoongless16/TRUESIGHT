import smtplib
from email.mime.text import MIMEText

def send_email_otp(email, otp):
    sender_email = "syazhsrm@gmail.com"
    sender_password = "pmkx mmie lkmu regv"
    smtp_server = "smtp.gmail.com"         # SMTP server for Gmail
    smtp_port = 587                        # Port number for TLS
    subject = "Test OTP Code"
    body = f"Your OTP Code is {otp}. It is valid for 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            print(f"Test email sent successfully to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise