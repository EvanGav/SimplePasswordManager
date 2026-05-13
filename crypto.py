import base64
import hmac
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS = 480_000
KEY_CHECK_PLAINTEXT = b"__vault_key_ok__"


def new_salt() -> bytes:
    return os.urandom(16)


def _pbkdf2(password: str, salt: bytes, length: int = 32) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode())


def derive_fernet_key(enc_key: str, salt: bytes) -> bytes:
    """Retourne une clé Fernet (base64url) dérivée de enc_key + salt."""
    return base64.urlsafe_b64encode(_pbkdf2(enc_key, salt))


def build_fernet(enc_key: str, salt: bytes) -> Fernet:
    return Fernet(derive_fernet_key(enc_key, salt))


def hash_access_password(password: str, salt: bytes) -> bytes:
    return _pbkdf2(password, salt, length=64)


def verify_access_password(password: str, salt: bytes, stored_hash: bytes) -> bool:
    return hmac.compare_digest(hash_access_password(password, salt), stored_hash)
