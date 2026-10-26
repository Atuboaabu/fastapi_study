from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from database import engine
from collections.abc import Callable

from models import User
from security import decode_access_token
from exceptions import InvalidTokenException, InactiveUserException, ForbiddenException


SessionFactory = Callable[[], Session]

def create_session()->Session:
    return Session(engine)

def get_seesion_factory()->SessionFactory:
    return create_session

SessionFactoryDep = Annotated[SessionFactory, Depends(get_seesion_factory)]

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

CurrentUserDep = Annotated[User, Depends(get_current_user)]

def get_current_active_user(
    current_user: CurrentUserDep
) -> User:
    if not current_user.is_active:
        raise InactiveUserException()
    
    return current_user

ActiveUserDep = Annotated[User, Depends(get_current_active_user)]

def get_current_admin_user(
    active_user: ActiveUserDep
) -> User:
    if active_user.role != "admin":
        raise ForbiddenException()
    
    return active_user

AdminUserDep = Annotated[User, Depends(get_current_admin_user)]