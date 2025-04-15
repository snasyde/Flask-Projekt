from app import db
import uuid
import os
import io
import base64
import pyotp
import qrcode
import base64
from app import config
from sqlalchemy.dialects.postgresql import JSON
import secrets

from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class Users(db.Model):
    """Datenbankmodell für Benutzer mit sicherer Passwort- und TOTP-Speicherung."""

    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), unique=True)
    email_2fa = db.Column(db.Boolean, default=False)
    totp_2fa = db.Column(db.Boolean, default=False)
    totp = db.Column(db.String(500), unique=True)
    salt = db.Column(db.LargeBinary(16), nullable=False, unique=True)
    backup_codes = db.Column(JSON, nullable=True)

    def __init__(self, username: str, password: str):
        self.username = username
        self.set_password(password)
        self.salt = os.urandom(16)
        self.totp = self._encrypt_totp(pyotp.random_base32())

    def set_password(self, password: str):
        """Hash das Passwort und speichert es."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Überprüft ein eingegebenes Passwort gegen den gespeicherten Hash."""
        return check_password_hash(self.password_hash, password)

    def verify_2fa(self, code: str) -> bool:
        """Validiert einen eingegebenen TOTP-Code."""
        try:
            secret = self._decrypt_totp()
            return pyotp.TOTP(secret).verify(code)
        except Exception:
            return False  # Optional: logging oder Fehlerbehandlung

    def get_totp_uri(self) -> str:
        """
        Erstellt einen provisioning URI für 2FA, nutzbar in Authenticator-Apps.
        """
        secret = self._decrypt_totp()
        return pyotp.TOTP(secret).provisioning_uri(name=self.username, issuer_name="AntonsFlaskProjekt")

    def get_totp_qr(self) -> str:
        """
        Generiert und zeigt den QR-Code zur TOTP-Einrichtung.
        """
        uri = self.get_totp_uri()
        qr = qrcode.make(uri)
        
        buffered = io.BytesIO()
        qr.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()

        return qr_base64

    def generate_backup_codes(self, count: int = 10, length: int = 10) -> list[str]:
            """
            Generiert einmalige Backup-Codes und speichert sie verschlüsselt.
            """
            codes = [str(secrets.randbelow(10**length)).zfill(length) for _ in range(count)]
            key = self._derive_key()
            fernet = Fernet(key)

            encrypted_codes = [fernet.encrypt(code.encode()).decode() for code in codes]
            self.backup_codes = encrypted_codes
            db.session.commit()  # Speichert die Backup-Codes in der DB

            return codes  # Gibt Klartextcodes zurück (z. B. für Download/Anzeige)

    def verify_backup_code(self, code: str) -> bool:
        """
        Überprüft, ob ein eingegebener Backup-Code gültig ist.
        Bei Erfolg wird der Code entfernt (Einmalnutzung).
        """
        if not self.backup_codes:
            return False

        key = self._derive_key()
        fernet = Fernet(key)

        for encrypted_code in self.backup_codes:
            try:
                decrypted = fernet.decrypt(encrypted_code.encode()).decode()
                if decrypted == code:
                    self.backup_codes.remove(encrypted_code)
                    return True
            except Exception:
                continue

        return False

    def _derive_key(self) -> bytes:
        """
        Leitet einen Schlüssel aus dem Benutzerpasswort und Salt für die TOTP-Verschlüsselung ab.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100_000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(config['secret_key'].encode()))

    def _encrypt_totp(self, secret: str) -> str:
        """
        Verschlüsselt den TOTP-Secret mit einem aus dem Passwort abgeleiteten Schlüssel.
        """
        key = self._derive_key()
        return Fernet(key).encrypt(secret.encode()).decode()

    def _decrypt_totp(self) -> str:
        """
        Entschlüsselt den gespeicherten TOTP-Secret.
        """
        key = self._derive_key()
        return Fernet(key).decrypt(self.totp.encode()).decode()