
def test_create_product(
    client,
    admin_headers
):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        },
        headers=admin_headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sku"] == "TEST-01"
    assert data["name"] == "Keyboard"
    assert data["price"] == 99.9
    assert data["stock"] == 10
    assert data["description"] == "Test keyboard"
    assert isinstance(data["id"], int)

def test_create_product_no_admin_headers(
    client,
    admin_headers
):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        }
    )

    assert response.status_code == 401

def test_create_product_customer_headers(
    client,
    customer_headers
):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        },
        headers = customer_headers
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "FORBIDDEN",
        "detail": "Insufficient permissions"
    }


def test_create_product_duplicate_sku(
    client,
    admin_headers
):
    first_response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        },
        headers = admin_headers
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard-2",
            "price": 999.9,
            "stock": 20,
            "description": "Test keyboard 2"
        },
        headers = admin_headers
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "code": "PRODUCT_SKU_EXISTS",
        "detail": "Product sku TEST-01 already exists"
    }

def test_create_product_invalid_price(
    client,
    admin_headers
):
    response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard-2",
            "price": -1,
            "stock": 20,
            "description": "Test keyboard 2"
        },
        headers = admin_headers
    )

    assert response.status_code == 422

    products_response = client.get(
        "/products/"
    )

    assert products_response.status_code == 200
    assert products_response.json() == []

def test_get_product(
        client,
        create_product
):
    product = create_product()

    assert product.id is not None

    response = client.get(
        f"/products/{product.id}"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == product.id
    assert data["sku"] == "TEST-01"
    assert data["name"] == "Keyboard"
    assert data["price"] == 99.9
    assert data["stock"] == 10
    assert data["description"] == None

def test_get_product_not_found(
        client
):
    response = client.get(
        f"/products/9999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "PRODUCT_NOT_FOUND",
        "detail": f"Product 9999 not found" 
    }

def test_get_products(
        client,
        create_product
):
    create_product()
    create_product(
        sku = "TEST-02",
        name = "Keyboard-2",
        price = 999.9,
        stock = 100,
        description = "Test product 2"
    )

    response = client.get(
        f"/products/"
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    products_by_sku = {
        item["sku"]: item
        for item in data
    }

    product1 = products_by_sku["TEST-01"]
    assert product1["name"] == "Keyboard"
    assert product1["price"] == 99.9
    assert product1["stock"] == 10
    assert product1["description"] == None

    product2 = products_by_sku["TEST-02"]
    assert product2["name"] == "Keyboard-2"
    assert product2["price"] == 999.9
    assert product2["stock"] == 100
    assert product2["description"] == "Test product 2"

def test_patch_product(
    client,
    create_product,
    admin_headers
):
    product = create_product()

    assert product.id is not None

    response = client.patch(
        f"/products/{product.id}",
        json = {
            "description": f"Patch product {product.id} test"
        },
        headers = admin_headers
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == product.id
    assert data["sku"] == "TEST-01"
    assert data["name"] == "Keyboard"
    assert data["price"] == 99.9
    assert data["stock"] == 10
    assert data["description"] == f"Patch product {product.id} test"

def test_put_product(
    client,
    create_product,
    admin_headers
):
    product = create_product()

    assert product.id is not None

    response = client.put(
        f"/products/{product.id}",
        json = {
            "sku": "TEST-PUT-01",
            "name": "Put-Keyboard",
            "price": 999.9,
            "stock": 20,
            "description": "Test PUT keyboard"
        },
        headers=admin_headers
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == product.id
    assert data["sku"] == "TEST-PUT-01"
    assert data["name"] == "Put-Keyboard"
    assert data["price"] == 999.9
    assert data["stock"] == 20
    assert data["description"] == "Test PUT keyboard"

def test_delete_product(
    client,
    create_product,
    admin_headers
):
    product = create_product()

    assert product.id is not None

    response = client.delete(
        f"/products/{product.id}",
        headers = admin_headers
    )
    assert response.status_code == 204

    response = client.get(
        f"/products/{product.id}"
    )
    assert response.status_code == 404

def test_delete_product_in_use(
    client,
    create_product,
    admin_headers
):
    product = create_product()

    assert product.id is not None

    order_response = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1
                }
            ]
        },
        headers = admin_headers
    )
    assert order_response.status_code == 201

    response = client.delete(
        f"/products/{product.id}",
        headers = admin_headers
    )
    assert response.status_code == 409

    assert response.json() == {
        "code": "PRODUCT_IN_USE",
        "detail": f"Product {product.id} in use"
    }

    response = client.get(
        f"/products/{product.id}"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == product.id
    assert data["sku"] == "TEST-01"
    assert data["name"] == "Keyboard"
    assert data["price"] == 99.9
    assert data["stock"] == 9
    assert data["description"] == None