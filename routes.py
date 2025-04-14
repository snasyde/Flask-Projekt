# Flask importieren
from flask import render_template, session, redirect, url_for, request, flash

# Datenbank-Model importieren
from models import Users

# Zufallszahlen-Modul importieren
import random

# Unterstützende Funktionen importieren
from utils import login_required, twofa_required, send_email

# Funktionsdefinition für die Registrierung von Routen
def register_routes(app, db):
    # Route zur Startseite
    @app.route('/')
    def index():
        return render_template('index.html')


    # Route zur Registrierung eines neuen Benutzers
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Falls bereits angemeldet, Weiterleitung zum Benutzerkonto
        if 'user' in session.keys():
            flash('Bereits angemeldet')
            return redirect(url_for('account'))
        
        # Registrierungseite anzeigen
        if request.method == 'GET':
            return render_template('register.html')
        
        # Registrierung verarbeiten
        elif request.method == 'POST':
            # Prüfen, ob der Benutzername bereits existiert
            if Users.query.filter_by(username=request.form['username']).first():
                flash('Benutzername bereits vergeben')
                return redirect(url_for('register'))
            
            else:
                # Neuen Benutzer in der Datenbank speichern
                user = Users(request.form['username'], request.form['password'])
                db.session.add(user)
                db.session.commit()

                # Benutzer in der Session speichern (automatisches Einloggen)
                session['username'] = request.form['username']
                flash('Benutzerkonto erfolgreich erstellt')
                return redirect(url_for('account'))


    # --------------------------------------------------
    # Route: /account
    # Zweck:
    #   - Anzeige des Benutzerkontos
    #   - Login-Vorgang inkl. 2FA-Weiterleitung bei aktivierter Zwei-Faktor-Authentifizierung
    # --------------------------------------------------
    @app.route('/account', methods=['GET', 'POST'])
    def account():

        # ----------------------------------------
        # GET-Anfrage: Seite anzeigen
        # ----------------------------------------
        if request.method == 'GET':
            # Benutzer bereits angemeldet?
            if 'username' in session:
                user = Users.query.get(session['username'])

                # 2FA bereits verifiziert oder nicht erforderlich
                if session.get('2fa_verified') or not user.twofa:
                    session['2fa_verified'] = False # 2FA-Status zurücksetzen
                    return render_template('account.html', user=user)
                else:
                    # 2FA aktiv, aber noch nicht abgeschlossen
                    flash('Bitte verifiziere deinen 2FA-Code.')
                    return redirect(url_for('twofa_verify'))
            else:
                # Noch nicht eingeloggt → Login-Seite anzeigen
                return render_template('login.html')

        # ----------------------------------------
        # POST-Anfrage: Login-Formular wurde abgeschickt
        # ----------------------------------------
        elif request.method == 'POST':
            # Prüfen, ob Login-Daten vorhanden sind
            user = Users.query.get(request.form['username'])

            # Benutzername existiert nicht
            if not user:
                flash('Benutzer nicht gefunden.')
                return redirect(url_for('account'))

             # Passwort stimmt nicht
            elif user.password != request.form['password']:
                flash('Falsches Passwort.')
                return redirect(url_for('account'))

            # Login erfolgreich
            else:
                session['username'] = user.username
                flash('Erfolgreich angemeldet.')

                return redirect(url_for('account'))

    
    
    # --------------------------------------------------
    # Route: /verify
    # Zweck:
    #   - Verifiziert den 2FA-Code, der an die E-Mail des Nutzers gesendet wurde.
    #   - Nur zugänglich, wenn der Benutzer eingeloggt ist (via @login_required).
    # --------------------------------------------------
    @app.route('/verify', methods=['GET', 'POST'])
    @login_required
    def twofa_verify():
        # Benutzer aus der Datenbank holen
        user = Users.query.filter_by(username=session['username']).first()

        # Wenn der Benutzer keine 2FA aktiviert hat
        if not user.twofa:
            flash('Zwei-Faktor-Authentifizierung ist für dich nicht aktiviert.')
            return redirect(url_for('account'))

        # Wenn 2FA bereits erfolgreich verifiziert wurde
        elif session.get('2fa_verified'):
            flash('Zwei-Faktor-Authentifizierung wurde bereits abgeschlossen.')
            return redirect(url_for('account'))

        # GET-Anfrage: Code generieren und per E-Mail senden
        if request.method == 'GET':
            session['code'] = str(random.randint(1000, 9999))  # 4-stelligen Code erzeugen
            code = session['code']

            # Senden der E-Mail mit dem Bestätigungscode
            flash(send_email(email=user.email,
                subject='Dein Zwei-Faktor-Code zur Bestätigung',

                message_plain=f'''
                Dein Bestätigungscode für die Zwei-Faktor-Authentifizierung lautet:
                {code}

                Bitte gib diesen Code auf der Website ein, um dich zu verifizieren.

                Wenn du diesen Code nicht selbst angefordert hast, wurde die Verifizierung möglicherweise von jemand anderem ausgelöst.
                In diesem Fall empfehlen wir dir, dein Passwort zu ändern.

                Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.
                ''',


                message_html=f'''
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <p>Dein <strong>Bestätigungscode</strong> für die Zwei-Faktor-Authentifizierung lautet:</p>
                        <p style="font-size: 18px; color: #0052cc;"><strong>{code}</strong></p>

                        <p>Bitte gib diesen Code auf der Website ein, um dich zu verifizieren.</p>

                        <p>Wenn du diesen Code nicht selbst angefordert hast, wurde die Verifizierung möglicherweise von jemand anderem ausgelöst.</p>
                        <p style="color: gray;">In diesem Fall empfehlen wir dir, dein Passwort zu ändern.</p>

                        <p style="color: gray;">Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.</p>
                    </body>
                </html>
                '''))
            
            return render_template('twofa_verify.html', action='twofa_verify')

        # POST-Anfrage: Code-Eingabe prüfen
        elif request.method == 'POST':
            if request.form['code'] == session['code']:
                session.pop('code', None)                     # Code aus Session entfernen
                session['2fa_verified'] = True          # 2FA-Status markieren
                flash('Zwei-Faktor-Authentifizierung erfolgreich verifiziert.')
                return redirect(url_for('account'))
            else:
                session.pop('code', None)                     # Bei falschem Code: löschen
                flash('Falscher Code, bitte erneut versuchen.')
                return redirect(url_for('twofa_verify'))


    # --------------------------------------------------
    # Route: /change_name
    # Zweck:
    #   - Ermöglicht dem Benutzer, seinen Benutzernamen zu ändern
    #   - Nutzer muss eingeloggt sein und 2FA verifiziert haben
    # --------------------------------------------------
    @app.route('/change_name', methods=['POST'])
    @login_required
    @twofa_required
    def change_name():
        # Überprüfen, ob der neue Benutzername bereits vergeben ist
        if Users.query.get(request.form['new_name']):
            flash('Benutzername bereits vergeben')  # Fehlernachricht, falls der Name schon existiert
            return redirect(url_for('account'))

        session['2fa_verified'] = False # 2FA-Status zurücksetzen

        # Benutzer-Objekt aus der Datenbank abrufen
        user = Users.query.get(session['user'])

        # Benutzernamen ändern
        user.username = request.form['new_name']
        db.session.commit()  # Änderungen in der Datenbank speichern

        # Benutzername in der Session aktualisieren
        session['username'] = request.form['new_name']

        # Bestätigung der Änderung
        flash('Benutzername geändert')
        return redirect(url_for('account'))


    # --------------------------------------------------
    # Route: /change_password
    # Zweck:
    #   - Ermöglicht es dem Benutzer, sein Passwort zu ändern
    #   - Benutzer muss eingeloggt und 2FA verifiziert haben
    # --------------------------------------------------
    @app.route('/change_password', methods=['POST'])
    @login_required
    @twofa_required
    def change_password():
        # Benutzer aus der Datenbank anhand des aktuellen Session-Nutzernamens abrufen
        user = Users.query.get(session['username'])

        # Überprüfen, ob das angegebene alte Passwort korrekt ist
        if request.form['old_password'] != user.password:
            flash('Falsches Passwort')  # Fehlermeldung, falls das alte Passwort falsch ist
            return redirect(url_for('account'))

        # Überprüfen, ob das neue Passwort gleich dem alten Passwort ist
        elif request.form['old_password'] == request.form['new_password']:
            flash('Neues Passwort darf nicht gleich dem alten Passwort sein')  # Fehlermeldung bei gleichbleibendem Passwort
            return redirect(url_for('account'))

        # Falls alle Prüfungen bestanden wurden, Passwort aktualisieren
        else:
            session['2fa_verified'] = False # 2FA-Status zurücksetzen
            user.password = request.form['new_password']  # Neues Passwort setzen
            db.session.commit()  # Änderungen in der Datenbank speichern

            flash('Passwort geändert')  # Erfolgsnachricht
            return redirect(url_for('account'))


    # --------------------------------------------------
    # Route: /change_email
    # Zweck:
    #   - Ermöglicht es dem Benutzer, seine E-Mail-Adresse zu ändern
    #   - Erfordert Login und 2FA-Verifizierung
    #   - Versendet einen Bestätigungscode an die neue E-Mail-Adresse
    # --------------------------------------------------
    @app.route('/change_email', methods=['POST'])
    @login_required
    @twofa_required
    def change_email():
        # Schritt 1: Neue E-Mail wurde eingegeben
        if 'new_email' in request.form.keys():
            # Prüfen, ob die E-Mail bereits registriert ist
            if Users.query.filter_by(email=request.form['new_email']).first():
                flash('E-Mail bereits vergeben')
                return redirect(url_for('account'))
            else:
                # Temporär speichern und Bestätigungscode generieren
                session['new_email'] = request.form['new_email']
                session['code'] = str(random.randint(1000, 9999))
                code = session['code']

                # Senden der Bestätigungs-E-Mail
                flash(send_email(
                    email=session['new_email'],
                    subject='Dein Code zur Bestätigung deiner E-Mail-Adresse',

                    message_plain=f'''
                    Dein Bestätigungscode für die Verifizierung deiner E-Mail-Adresse lautet:
                    {code}

                    Bitte gib diesen Code auf der Website ein, um deine E-Mail-Adresse zu bestätigen.

                    Wenn du diesen Code nicht selbst angefordert hast, kannst du die E-Mail einfach ignorieren.

                    Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.
                    ''',

                    message_html=f'''
                    <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                            <p>Dein <strong>Bestätigungscode</strong> für die Verifizierung deiner E-Mail-Adresse lautet:</p>
                            <p style="font-size: 18px; color: #0052cc;"><strong>{code}</strong></p>

                            <p>Bitte gib diesen Code auf der Website ein, um deine E-Mail-Adresse zu bestätigen.</p>

                            <p>Wenn du diesen Code nicht selbst angefordert hast, kannst du die E-Mail einfach ignorieren.</p>

                            <p style="color: gray;">Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.</p>
                        </body>
                    </html>
                    '''
                ))

                # Weiterleitung zur Code-Eingabeseite
                return render_template('twofa_verify.html', action='change_email')

        # Schritt 2: Benutzer hat den Bestätigungscode eingegeben
        elif 'code' in request.form.keys():
            # Code validieren
            if request.form['code'] == session['code']:
                Users.query.get(session['username']).email = session['new_email']
                db.session.commit()

                # Temporäre Sitzungsdaten löschen
                session.pop('new_email', None)
                session.pop('code', None)

                flash('E-Mail-Adresse erfolgreich geändert')
                return redirect(url_for('account'))
            else:
                # Ungültiger Code
                session.pop('new_email', None)
                session.pop('code', None)
                flash('Falscher Code')
                return redirect(url_for('account'))

 
    # --------------------------------------------------
    # Route: /delete_account
    # Zweck:
    #   - Ermöglicht es dem Benutzer, sein Konto zu löschen
    #   - Benutzer muss eingeloggt und 2FA verifiziert haben
    #   - Nach dem Löschen wird der Benutzer abgemeldet und auf die Registrierungsseite weitergeleitet
    # --------------------------------------------------
    @app.route('/delete_account', methods=['POST'])
    @login_required
    @twofa_required
    def delete_account():
        # Benutzer anhand des in der Session gespeicherten Benutzernamens aus der Datenbank abrufen
        user = Users.query.get(session['username'])

        # Überprüfen, ob das eingegebene Passwort mit dem in der Datenbank gespeicherten Passwort übereinstimmt
        if request.form["password"] == user.password:
            # Benutzerkonto aus der Datenbank löschen
            db.session.delete(user)
            db.session.commit()  # Änderungen in der Datenbank speichern

            # Session leeren, um den Benutzer abzumelden und alle Sitzungsdaten zu entfernen
            session.clear()

            # Erfolgsnachricht anzeigen
            flash('Account gelöscht')

            # Benutzer wird nach dem Löschen des Kontos zur Registrierungsseite weitergeleitet
            return redirect(url_for('register'))

        else:
            # Fehlermeldung, wenn das eingegebene Passwort nicht mit dem gespeicherten Passwort übereinstimmt
            flash('Falsches Passwort')

            # Benutzer wird zurück zur Account-Seite geleitet, um den Fehler zu korrigieren
            return redirect(url_for('account'))


    # --------------------------------------------------
    # Route: /forgot_password
    # Zweck:
    #   - Ermöglicht es einem Benutzer, sein Passwort zurückzusetzen
    #   - Benutzer gibt seine E-Mail-Adresse ein, um einen Bestätigungscode zu erhalten
    #   - Der Bestätigungscode wird an die angegebene E-Mail-Adresse gesendet
    #   - Benutzer gibt den Code ein, um das Passwort zurückzusetzen
    # --------------------------------------------------
    @app.route('/forgot_password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'GET':
            # GET-Anfrage: Zeigt das Formular zum Zurücksetzen des Passworts an
            return render_template('forgot_password.html')

        elif request.method == 'POST':
            if 'email' in request.form.keys():
                # POST-Anfrage: Benutzer gibt seine E-Mail-Adresse ein
                user = Users.query.filter_by(email=request.form['email']).first()

                # Prüfen, ob der Benutzer mit dieser E-Mail existiert
                if not user:
                    flash('Benutzer nicht gefunden')  # Fehlernachricht, wenn die E-Mail nicht existiert
                    return redirect(url_for('reset_password'))
                    
                else:
                    # Benutzer existiert: Einen Code generieren und in der Sitzung speichern
                    session['username'] = user.username
                    session['code'] = str(random.randint(1000, 9999))
                    code = session['code']

                    # Senden der E-Mail mit dem Bestätigungscode für das Zurücksetzen des Passworts
                    flash(send_email(email=user.email,
                        subject='Dein Zwei-Faktor-Code zur Passwortzurücksetzung',

                        # E-Mail im Klartext-Format
                        message_plain=f'''
                        Dein Bestätigungscode für die Passwortzurücksetzung lautet:
                        {code}

                        Bitte gib diesen Code auf der Website ein, um dein Passwort zurückzusetzen.

                        Wenn du diesen Code nicht selbst angefordert hast, wurde die Anfrage möglicherweise von jemand anderem ausgelöst.
                        In diesem Fall empfehlen wir dir, deine E-Mail sofort zu ändern, um dein Konto zu schützen.

                        Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.
                        ''',

                        # E-Mail im HTML-Format
                        message_html=f'''
                        <html>
                            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                                <p>Dein <strong>Bestätigungscode</strong> für die Passwortzurücksetzung lautet:</p>
                                <p style="font-size: 18px; color: #0052cc;"><strong>{code}</strong></p>

                                <p>Bitte gib diesen Code auf der Website ein, um dein Passwort zurückzusetzen.</p>

                                <p>Wenn du diesen Code nicht selbst angefordert hast, wurde die Anfrage möglicherweise von jemand anderem ausgelöst.</p>
                                <p style="color: gray;">In diesem Fall empfehlen wir dir, deine E-Mail sofort zu ändern, um dein Konto zu schützen.</p>

                                <p style="color: gray;">Achte darauf, den Code niemals an Dritte weiterzugeben, um dein Konto sicher zu halten.</p>
                            </body>
                        </html>
                        '''))

            elif 'code' in request.form.keys():
                # Wenn der Benutzer den Bestätigungscode eingibt
                if request.form['code'] == session['code']:
                    # Wenn der Code korrekt ist, wird das Passwort geändert
                    Users.query.get(session['username']).password = request.form['new_password']
                    db.session.commit()

                    # Code aus der Sitzung entfernen und Benutzer auf die Konto-Seite umleiten
                    session.pop('code', None)
                    flash('Passwort geändert')  # Bestätigungsmeldung für erfolgreiche Passwortänderung
                    return redirect(url_for('account'))
                else:
                    # Wenn der Code falsch ist, wird die Sitzung gelöscht und der Benutzer zurückgeschickt
                    session.clear()
                    flash('Falscher Code')  # Fehlermeldung für falschen Code
                    return redirect(url_for('reset_password'))


    # --------------------------------------------------
    # Route: /change_2fa
    # Zweck:
    #   - Ermöglicht es dem Benutzer, die Zwei-Faktor-Authentifizierung (2FA) zu aktivieren oder zu deaktivieren
    #   - Benutzer muss eingeloggt und 2FA verifiziert sein
    # --------------------------------------------------
    @app.route('/change_2fa')
    @login_required
    @twofa_required
    def change_2fa():
        # Benutzer aus der Datenbank anhand des in der Session gespeicherten Benutzernamens abrufen
        user = Users.query.get(session['username'])

        # Überprüfen, ob der Benutzer bereits die Zwei-Faktor-Authentifizierung aktiviert hat
        if user.twofa:
            # Deaktivieren der 2FA, falls sie aktiviert ist
            user.twofa = False
            db.session.commit()  # Änderungen in der Datenbank speichern
            flash('Zwei-Faktor-Authentifizierung deaktiviert')  # Erfolgsnachricht anzeigen
        else:
            # Falls der Benutzer keine E-Mail-Adresse angegeben hat, 2FA nicht aktivieren
            if not user.email:
                flash('Bitte zuerst E-Mail-Adresse angeben')  # Fehlermeldung anzeigen, wenn keine E-Mail vorhanden
                return redirect(url_for('account'))  # Zurück zur Account-Seite, um die E-Mail zu setzen
            
            # Aktivieren der Zwei-Faktor-Authentifizierung, wenn sie nicht aktiviert ist
            user.twofa = True
            db.session.commit()  # Änderungen in der Datenbank speichern
            flash('Zwei-Faktor-Authentifizierung aktiviert')  # Erfolgsnachricht anzeigen

        session['2fa_verified'] = False # 2FA-Status zurücksetzen

        # Nach der Änderung der 2FA-Einstellungen zurück zur Account-Seite weiterleiten
        return redirect(url_for('account'))


    # --------------------------------------------------
    # Route: /log_out
    # Zweck:
    #   - Ermöglicht es dem Benutzer, sich abzumelden
    #   - Löscht die Sitzung und leitet den Benutzer zurück zur Account-Seite
    # --------------------------------------------------
    @app.route('/log_out')
    @login_required
    def log_out():
        # Alle Daten in der Session löschen, um den Benutzer abzumelden
        session.clear()

        # Erfolgsnachricht anzeigen, dass der Benutzer erfolgreich abgemeldet wurde
        flash('Erfolgreich abgemeldet')

        # Benutzer nach der Abmeldung zurück zur Account-Seite weiterleiten
        return redirect(url_for('account'))


    # Route erstellen: Spiel starten
    @app.route('/play')
    @login_required
    def play():
        return render_template('game.html')