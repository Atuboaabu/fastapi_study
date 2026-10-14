import jwt
from datetime import datetime, timezone, timedelta
from config import settings

from models import User

def test_get_me(
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
    user_id = register_response.json()["id"]

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

    response = client.get(
        "/users/me",
        headers = {
            "Authorization": (
                f"Bearer {token["access_token"]}"
            ),
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "user1"
    assert "hashed_password" not in data

def test_get_me_no_authorization_header(
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
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    
    token = login_response.json()
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str)

    response = client.get(
        "/users/me",
    )
    assert response.status_code == 401

def test_get_me_invalid_token(
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
    user_id = register_response.json()["id"]

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

    bad_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc)
                + timedelta(minutes=30),
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/users/me",
        headers = {
            "Authorization": (
                f"Bearer {bad_token}"
            ),
        }
    )
    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_TOKEN",
        "detail": "Token is invalid"
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_get_me_expire(
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
    user_id = register_response.json()["id"]

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

    bad_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc)
                - timedelta(minutes=30),
        },
        key = settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/users/me",
        headers = {
            "Authorization": (
                f"Bearer {bad_token}"
            ),
        }
    )
    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_TOKEN",
        "detail": "Token is invalid"
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_get_me_unknown_user(
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
    user_id = register_response.json()["id"]

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

    bad_token = jwt.encode(
        {
            "sub": "9999",
            "exp": datetime.now(timezone.utc)
                + timedelta(minutes=30),
        },
        key = settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/users/me",
        headers = {
            "Authorization": (
                f"Bearer {bad_token}"
            ),
        }
    )
    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_TOKEN",
        "detail": "Token is invalid"
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_get_me_inactive(
    client,
    session
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]
    user = session.get(User, user_id)
    assert user is not None
    user.is_active = False
    session.commit()

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

    response = client.get(
        "/users/me",
        headers = {
            "Authorization": (
                f"Bearer {token["access_token"]}"
            ),
        }
    )
    assert response.status_code == 403
    assert response.json() == {
        "code": "USER_INACTIVE",
        "detail": "User is inactive"
    }

def test_get_admin_customer(
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
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    
    token = login_response.json()
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str)

    response = client.get(
        "/users/admin-check",
        headers = {
            "Authorization": (
                f"Bearer {token["access_token"]}"
            ),
        }
    )
    assert response.status_code == 403
    assert response.json() == {
        "code": "FORBIDDEN",
        "detail": "Insufficient permissions"
    }

def test_get_admin_success(
    client,
    session
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    user = session.get(User, user_id)
    assert user is not None
    user.role = "admin"
    session.commit()

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

    response = client.get(
        "/users/admin-check",
        headers = {
            "Authorization": (
                f"Bearer {token["access_token"]}"
            ),
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "user1"
    assert data["is_active"] == True
    assert data["role"] == "admin"

def test_get_admin_inactive(
    client,
    session
):
    register_response = client.post(
        "/auth/register",
        json = {
            "username": "user1",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    user = session.get(User, user_id)
    assert user is not None
    user.is_active = False
    session.commit()

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

    response = client.get(
        "/users/admin-check",
        headers = {
            "Authorization": (
                f"Bearer {token["access_token"]}"
            ),
        }
    )
    assert response.status_code == 403
    assert response.json() == {
        "code": "USER_INACTIVE",
        "detail": "User is inactive"
    }
