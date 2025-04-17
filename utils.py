# --------------------------------------------------
# Imports
# --------------------------------------------------

# Flask & Session-Handling
from functools import wraps
from flask import session, redirect, url_for, flash

# Datenbankmodell
from models import Users

# --------------------------------------------------
# Decorator: login_required
# Zweck:
#   - Stellt sicher, dass der Benutzer eingeloggt ist
#   - Wenn nicht, wird zur Account-Seite umgeleitet
# --------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melde dich zuerst an.')
            return redirect(url_for('account.index'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# Decorator: twofa_required
# Zweck:
#   - Stellt sicher, dass der Benutzer 2FA abgeschlossen hat
#   - Nur relevant für Benutzer, bei denen 2FA aktiviert ist
#   - Leitet zur 2FA-Verifizierung um, wenn nicht bestätigt
# --------------------------------------------------
def twofa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = Users.query.get(session['user_id'])
        if user.email_2fa and not session.get('2fa_verified') or user.totp_2fa and not session.get('2fa_verified'):
            flash('Zwei-Faktor-Authentifizierung erforderlich.')
            return redirect(url_for('account.twofa_verify'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# Decorator: admin_required
# Zweck:
#   - Stellt sicher, dass der Benutzer ein Admin ist
#   - Wenn nicht, wird zur Haupt-Seite umgeleitet
# --------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = Users.query.get(session['user_id'])
        if user.role != 'admin':
            flash('Zugriff verweigert. Nur Administratoren haben Zugriff auf diese Seite.')
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# E-Mail-Funktionalität
# --------------------------------------------------

# E-Mail-Versand über SMTP
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Konfiguration laden
from app import config

# --------------------------------------------------
# Funktion: send_email
# Zweck:
#   - Versendet eine E-Mail mit optionaler HTML-Version
#   - Parameter:
#       - email: Empfängeradresse
#       - subject: Betreff der E-Mail
#       - message_plain: Textversion der Nachricht (Pflicht)
#       - message_html: HTML-Version der Nachricht (optional)
# Rückgabe:
#   - Erfolgsmeldung oder Fehlermeldung als String
# --------------------------------------------------
def send_email(email: str, subject: str, message_plain: str, message_html: str = None) -> str:
    try:
        # Verbindung zum SMTP-Server aufbauen
        server = smtplib.SMTP(config['email_server'], config['email_port'])
        server.starttls()
        server.login(config['email_address'], config['email_password'])

        # E-Mail zusammenstellen
        msg = MIMEMultipart("alternative")
        msg['From'] = config['email_address']
        msg['To'] = email
        msg['Subject'] = subject

        # Textinhalt hinzufügen
        msg.attach(MIMEText(message_plain, 'plain'))

        # HTML-Inhalt hinzufügen, falls vorhanden
        if message_html:
            msg.attach(MIMEText(message_html, 'html'))

        # E-Mail versenden
        server.send_message(msg)
        server.quit()

        return 'E-Mail gesendet'

    except Exception as e:
        return f'Fehler: {e}'