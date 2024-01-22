import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body, to_email):
    smtp_server = 'smtp.gmail.com'  # Servidor SMTP de Gmail
    smtp_port = 587  # Puerto SMTP, generalmente 587 para TLS

    sender_email = 'djsertek@gmail.com'
    sender_password = 'yijlkxsukellhyqp'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = 'sergio@neural.one'
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())

# Luego, puedes enviar el correo en cualquier punto del código
subject = 'Mensaje de prueba'
body = 'Este es un mensaje de prueba enviado desde Python.'
to_email = 'sergio@neural.one'

send_email(subject, body, to_email)

