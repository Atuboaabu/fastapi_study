from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError

from models import User
from schemas import UserCreate

from exceptions import UsernameExistsException, InvalidCredentialsException
from security import hash_password, verify_password

def create_user(
    user_data: UserCreate,
    session: Session
) -> User:
    statement = select(User).where(
        User.username == user_data.username
    )
    user_get = session.exec(statement).first()
    if user_get is not None:
        raise UsernameExistsException(user_data.username)
    
    hashed_password = hash_password(user_data.password)

    user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    session.add(user)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise UsernameExistsException(user_data.username)
    session.refresh(user)

    return user

def authenticate_user(
    username: str,
    password: str,
    session: Session
) -> User:
    statement = select(User).where(
        User.username == username
    )
    user = session.exec(statement).first()
    if user is None:
        raise InvalidCredentialsException()
    
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()
    
    return user