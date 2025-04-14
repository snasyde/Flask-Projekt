# Datenbank-Instanz importieren
from app import db

# --------------------------------------------------
# Datenbankmodell: Users
# Repräsentiert einen Benutzer im System
# --------------------------------------------------
class Users(db.Model):
    # Benutzername als Primärschlüssel (Pflichtfeld)
    username = db.Column("Benutzername", db.Text, nullable=False, primary_key=True)
    
    # Passwort (Pflichtfeld)
    password = db.Column("Passwort", db.Text, nullable=False)
    
    # E-Mail-Adresse (optional)
    email = db.Column("E-Mail", db.Text)
    
    # Zwei-Faktor-Authentifizierung (Standard: deaktiviert)
    twofa = db.Column("2FA", db.Boolean, default=False)

    # Konstruktor zur Initialisierung eines Benutzers mit Benutzername und Passwort
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password