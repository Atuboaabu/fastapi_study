from sqlmodel import select

from models import User
from security import verify_password

def test_register_user_success(
    client,
    session
):
    user_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    
    assert user_response.status_code == 201
    user_data = user_response.json()
    assert user_data["username"] == "user1"
    assert user_data["is_active"] == True

    assert "password" not in user_data
    assert "hashed_password" not in user_data

    user = session.exec(
        select(User).where(
            User.username == "user1"
        )
    ).first()
    assert user is not None
    assert user.hashed_password != "password123"
    assert verify_password("password123", user.hashed_password)

def test_register_user_duplicatename(
    client
):
    user_response1 = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    
    assert user_response1.status_code == 201
    
    user_response2 = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password456"
        }
    )
    assert user_response2.status_code == 409
    assert user_response2.json() == {
        "code": "USERNAME_EXISTS",
        "detail": "Username user1 already exists"
    }

def test_register_user_invalid_pswd(
    client
):
    user_response1 = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "pswd"
        }
    )
    
    assert user_response1.status_code == 422