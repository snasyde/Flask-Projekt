# --------------------------------------------------
# Hauptprogramm: Anwendung starten
# --------------------------------------------------

# Flask-App, Datenbank und Konfiguration importieren
from app import create_app, db, config

# Flask-Anwendung erstellen
app = create_app()

# Wenn das Skript direkt ausgeführt wird (nicht importiert)
if __name__ == '__main__':

    # Anwendungskontext aktivieren und Datenbanktabellen erzeugen
    with app.app_context():
        db.create_all()

    # Flask-Entwicklungsserver starten mit Konfiguration aus config.json
    app.run(
        host=config['host'],
        port=config['port'],
        debug=config['debug']
    )