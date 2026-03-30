import hashlib
import os

_ITERATIONS = 120_000


def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    return pwd_hash.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    if not stored_hash or not stored_salt:
        return False
    salt = bytes.fromhex(stored_salt)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    return pwd_hash.hex() == stored_hash
