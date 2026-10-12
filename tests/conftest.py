import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from main import app
from dependencies import get_session
import models

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False
        },
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
    
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def client(session: Session):
    def get_test_session():
        yield session
    
    app.dependency_overrides[get_session] = get_test_session

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
        items: list[dict]
    ):
        response = client.post(
            "/orders/",
            json = {
                "items": items
            }
        )
        assert response.status_code == 201
        return response.json()
    
    return _create_order