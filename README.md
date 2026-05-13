# Password Manager

A local, offline password manager with a native GUI (tkinter). Passwords are encrypted at rest and never stored in plain text.

Quick note : <br>
- The app is in french, I kinda use it for certain non important passwords
- If you use this app, keep the password.json file in a safeplace
- Be sure you know the password and keep you set and never forget it (or store them in the safest place you know)
- Do NOT use it for important passwords, it's not made for that
---

## Features

- AES-based encryption (Fernet) with a key you alone know
- Two-factor protection: an access password (hashed) + a separate encryption key (never stored)
- Add, look up, copy, and delete entries through a tabbed GUI
- Batch entry: queue multiple passwords before committing a single save

---

## Requirements

- Python 3.11+
- [`cryptography`](https://pypi.org/project/cryptography/) ≥ 42.0

Install the dependency:

```bash
pip install -r requirements.txt
```

---

## Getting Started

```bash
cd ...
python main.py
```

### First run

You will be asked to create two credentials:

| Credential | Stored? | Purpose |
|---|---|---|
| **Access password** | Hashed (PBKDF2-SHA256, 480 000 iterations) | Proves your identity at startup |
| **Encryption key** | Never — RAM only | Derives the Fernet key used to encrypt/decrypt every password |

Both are required on every subsequent launch. Losing the encryption key makes the vault permanently unreadable.

---

## How It Works

```
Access password  ──PBKDF2──►  hash  ──stored in passwords.json (verification only)

Encryption key   ──PBKDF2──►  Fernet key  ──kept in RAM during the session
                                              └─► encrypts / decrypts vault entries
```

A `key_check` ciphertext is stored in the vault and decrypted at login to validate the encryption key without storing it anywhere.

The vault file structure:

```json
{
  "auth_salt":  "<base64>",
  "auth_hash":  "<base64>",
  "enc_salt":   "<base64>",
  "key_check":  "<base64 Fernet token>",
  "passwords": {
    "github":  "<base64 Fernet token>",
    "netflix": "<base64 Fernet token>"
  }
}
```

---

## Security Notes

- The encryption key is **never written to disk** — only held in memory for the duration of the session.
- Key derivation uses **PBKDF2-HMAC-SHA256 with 480 000 iterations** and a random 16-byte salt, making brute-force attacks expensive.
- Password comparison uses `hmac.compare_digest` to prevent timing attacks.
- The vault file is useless without both credentials.
