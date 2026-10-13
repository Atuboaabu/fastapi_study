import pytest
from services.users import authenticate_user
from security import hash_password
from models import User
from exceptions import InvalidCredentialsException

def test_authenticate_user_success(
    session
):
    user = User(
        username="user1",
        hashed_password=hash_password("password123")
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    auth_user = authenticate_user(
        "user1",
        "password123",
        session
    )

    assert auth_user is not None
    assert auth_user.id == user.id

def test_authenticate_user_wrong_pswd(
    session
):
    user = User(
        username="user1",
        hashed_password=hash_password("password123")
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    
    with pytest.raises(
        InvalidCredentialsException
    ):
        authenticate_user(
            "user1",
            "wrong_pswd",
            session
        )

def test_authenticate_user_unknown_user(
    session
):
    user = User(
        username="user1",
        hashed_password=hash_password("password123")
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    
    with pytest.raises(
        InvalidCredentialsException
    ):
        authenticate_user(
            "user2",
            "password123",
            session
        )