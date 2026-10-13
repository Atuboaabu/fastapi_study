import jwt
from sqlmodel import select

from models import User
from security import verify_password

from config import settings

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

def test_login_success(
    client
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    user_id = user_data["id"]

    login_response = client.post(
        "/auth/token",
        data = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    
    token = login_response.json()
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str)
    payload = jwt.decode(
        jwt = token["access_token"],
        key = settings.jwt_secret_key,
        algorithms = [settings.jwt_algorithm]
    )
    assert "sub" in payload
    assert "exp" in payload
    assert payload["sub"] == str(user_id)

def test_login_wrong_pswd(
    client
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        data = {
            "username": "user1",
            "password": "wrong_pswd"
        }
    )
    assert login_response.status_code == 401
    assert login_response.json() == {
        "code": "INVALID_CREDENTIALS",
        "detail": "Invalid username or password"
    }
    assert login_response.headers["www-authenticate"] == "Bearer"

def test_login_unknown_user(
    client
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        data = {
            "username": "unknown_user",
            "password": "password123"
        }
    )
    assert login_response.status_code == 401
    assert login_response.json() == {
        "code": "INVALID_CREDENTIALS",
        "detail": "Invalid username or password"
    }
    assert login_response.headers["www-authenticate"] == "Bearer"