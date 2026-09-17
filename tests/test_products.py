
def test_create_product(client):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sku"] == "TEST-01"
    assert data["name"] == "Keyboard"
    assert data["price"] == 99.9
    assert data["stock"] == 10
    assert data["description"] == "Test keyboard"
    assert isinstance(data["id"], int)

def test_create_product_duplicate_sku(client):
    client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        },
    )
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard-2",
            "price": 999.9,
            "stock": 20,
            "description": "Test keyboard 2"
        },
    )

    assert response.status_code == 409

    content = response.json()

    assert content["code"] == "PRODUCT_SKU_EXISTS"

def test_create_product_invalid_price(client):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard-2",
            "price": -1,
            "stock": 20,
            "description": "Test keyboard 2"
        },
    )

    assert response.status_code == 422