
def test_create_order(client):
    # 1、先创建一个 product
    product_response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        }
    )
    assert product_response.status_code == 201
    product_data = product_response.json()
    assert isinstance(product_data["id"], int)

    product_id = product_data["id"]
    # 创建order
    order_response = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ]
        }
    )
    
    assert order_response.status_code == 201
    order_data = order_response.json()

    assert order_data["status"] == "pending"
    assert isinstance(order_data["id"], int)

    order_items = order_data["items"]

    assert isinstance(order_items, list)

    assert len(order_items) == 1

    assert order_items[0]["product_id"] == product_id
    assert order_items[0]["quantity"] == 2
    assert isinstance(order_items[0]["id"], int)

    # get product 判断 stock 真实变化
    product_get_response = client.get(
        f"/products/{product_id}"
    )
    assert product_get_response.json()["stock"] == 8

def test_create_order_duplicate_product(client):
    # 1、先创建一个 product
    product_response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        }
    )
    assert product_response.status_code == 201
    product_data = product_response.json()
    assert isinstance(product_data["id"], int)

    product_id = product_data["id"]
    # 创建order
    order_response = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                },
                {
                    "product_id": product_id,
                    "quantity": 4
                }
            ]
        }
    )
    
    assert order_response.status_code == 400
    assert order_response.json() == {
        "code": "PRODUCT_DUPLICATE",
        "detail": "Duplicate product in order" 
    }

    # get product 判断 stock 没有变化
    product_get_response = client.get(
        f"/products/{product_id}"
    )
    assert product_get_response.json()["stock"] == 10

    # get orders 判断没有创建order
    get_orders_response = client.get(
        "/orders/"
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0

def test_create_order_no_product(client):
    # 创建order
    order_response = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2
                }
            ]
        }
    )
    
    assert order_response.status_code == 404
    assert order_response.json() == {
        "code": "PRODUCT_NOT_FOUND",
        "detail": f"Product 1 not found" 
    }

    # get orders 判断没有创建order
    get_orders_response = client.get(
        "/orders/"
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0

def test_create_order_insufficient_stock(client):
    # 1、先创建一个 product
    product_response = client.post(
        "/products/",
        json = {
            "sku": "TEST-01",
            "name": "Keyboard",
            "price": 99.9,
            "stock": 10,
            "description": "Test keyboard"
        }
    )
    assert product_response.status_code == 201
    product_data = product_response.json()
    assert isinstance(product_data["id"], int)

    product_id = product_data["id"]
    # 创建order
    order_response = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 12
                }
            ]
        }
    )
    
    assert order_response.status_code == 409
    assert order_response.json() == {
        "code": "PRODUCT_STOCK_INSUFFICIENT",
        "detail": f"Insufficient stock for product {product_id}"
    }

    # get product 判断 stock 没有变化
    product_get_response = client.get(
        f"/products/{product_id}"
    )
    assert product_get_response.json()["stock"] == 10

    # get orders 判断没有创建order
    get_orders_response = client.get(
        "/orders/"
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0