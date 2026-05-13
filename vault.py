import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

import crypto

VAULT_FILE = Path(__file__).parent / "passwords.json"


@dataclass
class Vault:
    auth_salt: bytes
    auth_hash: bytes
    enc_salt: bytes
    key_check: str
    passwords: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "auth_salt": base64.b64encode(self.auth_salt).decode(),
            "auth_hash": base64.b64encode(self.auth_hash).decode(),
            "enc_salt":  base64.b64encode(self.enc_salt).decode(),
            "key_check": self.key_check,
            "passwords": self.passwords,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Vault":
        return cls(
            auth_salt=base64.b64decode(data["auth_salt"]),
            auth_hash=base64.b64decode(data["auth_hash"]),
            enc_salt= base64.b64decode(data["enc_salt"]),
            key_check=data["key_check"],
            passwords=data.get("passwords", {}),
        )

    def save(self) -> None:
        with open(VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls) -> "Vault":
        with open(VAULT_FILE, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def encrypt_password(self, fernet: Fernet, plaintext: str) -> str:
        return fernet.encrypt(plaintext.encode()).decode()

    def decrypt_password(self, fernet: Fernet, site: str) -> str:
        return fernet.decrypt(self.passwords[site].encode()).decode()

    def add(self, fernet: Fernet, site: str, plaintext: str) -> None:
        self.passwords[site] = self.encrypt_password(fernet, plaintext)

    def remove(self, site: str) -> None:
        del self.passwords[site]

def vault_exists() -> bool:
    return VAULT_FILE.exists()


def create_vault(access_pw: str, enc_key: str) -> tuple["Vault", Fernet]:
    """Crée un nouveau vault et retourne (vault, fernet)."""
    auth_salt = crypto.new_salt()
    enc_salt  = crypto.new_salt()

    fernet    = crypto.build_fernet(enc_key, enc_salt)
    key_check = fernet.encrypt(crypto.KEY_CHECK_PLAINTEXT).decode()

    vault = Vault(
        auth_salt=auth_salt,
        auth_hash=crypto.hash_access_password(access_pw, auth_salt),
        enc_salt=enc_salt,
        key_check=key_check,
    )
    vault.save()
    return vault, fernet


def unlock_vault(access_pw: str, enc_key: str) -> tuple["Vault", Fernet]:
    """Charge et vérifie le vault. Lève ValueError si les identifiants sont incorrects."""
    vault = Vault.load()

    if not crypto.verify_access_password(access_pw, vault.auth_salt, vault.auth_hash):
        raise ValueError("Mot de passe d'accès incorrect.")

    fernet = crypto.build_fernet(enc_key, vault.enc_salt)
    try:
        fernet.decrypt(vault.key_check.encode())
    except InvalidToken:
        raise ValueError("Clé de chiffrement incorrecte.")

    return vault, fernet
