from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from database import engine

from models import User
from security import decode_access_token
from exceptions import InvalidTokenException

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl = "/auth/token"
)

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep
) -> User:
    user_id = decode_access_token(token)

    user = session.get(User, user_id)

    if user is None:
        raise InvalidTokenException()
    
    return user

CurretUserDep = Annotated[User, Depends(get_current_user)]