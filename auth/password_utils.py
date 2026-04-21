import os
import base64
import hashlib
import hmac


def hash_password(password):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return base64.b64encode(salt + hashed).decode("utf-8")


def verify_password(password, stored_hash):
    try:
        decoded = base64.b64decode(stored_hash.encode("utf-8"))
    except Exception:
        return False
    if len(decoded) < 48:
        return False
    salt = decoded[:16]
    stored = decoded[16:]
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return hmac.compare_digest(stored, computed)
