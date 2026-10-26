import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from sqlalchemy import Engine, event
from fastapi.testclient import TestClient

from main import app
from dependencies import get_session, get_seesion_factory, SessionFactory
import models
from security import hash_password, create_access_token

@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )
        cursor.close()

    SQLModel.metadata.create_all(engine)
    yield engine

    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def session(engine: Engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def create_session(engine: Engine):
    def _create_session()->Session:
        return Session(engine)
    
    return _create_session

@pytest.fixture
def client(session: Session, create_session: SessionFactory):
    def get_test_session():
        yield session
    
    def get_test_session_factory():
        return create_session

    app.dependency_overrides[get_session] = get_test_session
    app.dependency_overrides[get_seesion_factory] = get_test_session_factory

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()

@pytest.fixture
def create_product(session: Session):
    def _create_product(
            *,
            sku: str = "TEST-01",
            name: str = "Keyboard",
            price: float = 99.9,
            stock: int = 10,
            description: str | None = None
    ) -> models.Product:
        product = models.Product(
            sku = sku,
            name = name,
            price = price,
            stock = stock,
            description = description
        )

        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    return _create_product

@pytest.fixture
def create_order(client):
    def _create_order(
        *,
        items: list[dict],
        headers: dict
    ):
        response = client.post(
            "/orders/",
            json = {
                "items": items
            },
            headers = headers
        )
        assert response.status_code == 201
        return response.json()
    
    return _create_order

@pytest.fixture
def admin_headers(session: Session):
    user = models.User(
        username = "admin",
        hashed_password = hash_password("password123"),
        role = "admin"
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None

    token = create_access_token(
        str(user.id)
    )
    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def customer_headers(session: Session):
    user = models.User(
        username = "customer",
        hashed_password = hash_password("password123"),
        role = "customer"
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None

    token = create_access_token(
        str(user.id)
    )
    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def create_auth_user(session):
    def _create_auth_user(
        *,
        username: str,
        role: str = "customer"
    ):
        user = models.User(
            username = username,
            hashed_password = hash_password(
                "password123"
            ),
            role = role,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        access_token = create_access_token(
            str(user.id)
        )

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        return user, headers
    return _create_auth_user