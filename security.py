import jwt
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError

from config import settings
from exceptions import InvalidTokenException

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
        payload = payload,
        key = settings.jwt_secret_key,
        algorithm = settings.jwt_algorithm
    )

def decode_access_token(
    token: str
) -> int:
    try:
        payload = jwt.decode(
            jwt = token,
            key = settings.jwt_secret_key,
            algorithms = settings.jwt_algorithm,
            options = {
                "require" : ["sub", "exp"]
            }
        )
        subject = payload["sub"]

        return int(subject)
    except (
        KeyError,
        ValueError,
        InvalidTokenError
    ):
        raise InvalidTokenException()