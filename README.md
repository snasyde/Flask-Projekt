# Flask-Projekt

Dieses Projekt ist eine einfache Flask-Anwendung, die als Ausgangspunkt für Webanwendungen dient.

## Installation

1. Klone dieses Repository:
   ```bash
   git clone https://github.com/snasyde/Flask-Projekt.git
   cd Flask-Projekt

2. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt

3. Erstelle eine Konfigurationsdatei config.json im Hauptverzeichnis mit folgendem Aufbau:
```json
{
    "secret_key": "",

    "host": "",
    "port": 5000,
    "debug": true,

    "email_server": "",
    "email_port": 587,
    "email_address": "",
    "email_password": ""
}
```

4. Anwendung starten
```python
python main.py
