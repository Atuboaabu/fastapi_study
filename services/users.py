from sqlmodel import select
from sqlalchemy.exc import IntegrityError

from models import User
from schemas import UserCreate
from dependencies import SessionDep
from exceptions import UsernameExistsException
from security import hash_password

def create_user(
    user_data: UserCreate,
    session: SessionDep
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