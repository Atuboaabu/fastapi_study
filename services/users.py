from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError

from models import User
from schemas import UserCreate

from exceptions import UsernameExistsException, InvalidCredentialsException
from security import hash_password, verify_password
from services.result import UserResult

def create_user_operation(
    session: Session,
    args: list
) -> UserResult:
    assert len(args) > 0

    user_data = args[0]

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
    session.flush()

    assert user.id is not None

    session.refresh(user)

    return UserResult(
        user.id,
        user.username,
        user.hashed_password,
        user.is_active,
        user.role
    )

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