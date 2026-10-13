import jwt
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone

from config import settings

password_hash = PasswordHash.recommended()

def hash_password(
    password: str
) -> str:
    return password_hash.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(
    subject: str
) -> str:
    expire = (
        datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": subject,
        "exp": expire
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )