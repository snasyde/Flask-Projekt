# --------------------------------------------------
# Bibliotheken importieren
# --------------------------------------------------
import json                                  # Zum Laden der Konfigurationsdatei
from flask import Flask                      # Flask-Framework importieren
from flask_sqlalchemy import SQLAlchemy      # ORM für Datenbankzugriffe

# --------------------------------------------------
# Konfigurationsdaten aus JSON-Datei laden
# --------------------------------------------------
with open('config.json', "r") as file:
    config = json.load(file)

# --------------------------------------------------
# Datenbank-Objekt initialisieren
# --------------------------------------------------
db = SQLAlchemy()

# --------------------------------------------------
# Flask-App erstellen und konfigurieren
# --------------------------------------------------
def create_app():
    # Neue Flask-App instanziieren
    app = Flask(__name__, static_url_path='/')

    # Konfiguration setzen
    app.secret_key = config['secret_key']                             # Geheimschlüssel für Sessions
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'     # SQLite-Datenbankpfad

    # Datenbank mit der App verbinden
    db.init_app(app)

    # Routen importieren und registrieren
    from routes import register_routes
    register_routes(app, db)

    # App zurückgeben
    return app