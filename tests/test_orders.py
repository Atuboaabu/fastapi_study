
def test_create_order(
    client,
    create_product
):
    # 1、先创建一个 product
    product = create_product()
    assert product.id is not None

    product_id = product.id
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

def test_create_order_duplicate_product(
    client,
    create_product
):
    # 1、先创建一个 product
    product = create_product()
    assert product.id is not None

    product_id = product.id
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

def test_create_order_insufficient_stock(
    client,
    create_product
):
    # 1、先创建一个 product
    product = create_product()
    assert product.id is not None

    product_id = product.id
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

def test_get_orders_default_sort_desc(
    client,
    create_product
):
    product = create_product()
    assert product.id is not None

    product_id = product.id

    order1 = client.post(
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
    assert order1.status_code == 201

    order2 = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 4
                }
            ]
        }
    )
    assert order2.status_code == 201

    orders = client.get("/orders/")
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert orders_items[0]["id"] > orders_items[1]["id"]
    assert orders_items[0]["items"][0]["quantity"] == 4
    assert orders_items[1]["items"][0]["quantity"] == 2
    
    assert orders_data["total"] == 2
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20

    product_after = client.get(f"/products/{product_id}")
    assert product_after.status_code == 200
    product_after_data = product_after.json()
    assert product_after_data["stock"] == 4 # 10 - 2 - 4

def test_get_orders_sort_asc(
    client,
    create_product
):
    product = create_product()
    assert product.id is not None

    product_id = product.id

    order1 = client.post(
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
    assert order1.status_code == 201

    order2 = client.post(
        "/orders/",
        json = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 4
                }
            ]
        }
    )
    assert order2.status_code == 201

    orders = client.get(
        "/orders/?sort_order=asc"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert orders_items[0]["id"] < orders_items[1]["id"]
    assert orders_items[0]["items"][0]["quantity"] == 2
    assert orders_items[1]["items"][0]["quantity"] == 4
    
    assert orders_data["total"] == 2
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20

    product_after = client.get(f"/products/{product_id}")
    assert product_after.status_code == 200
    product_after_data = product_after.json()
    assert product_after_data["stock"] == 4 # 10 - 2 - 4

def test_get_orders_pagination(
    client,
    create_product
):
    product = create_product(stock=100)
    assert product.id is not None

    product_id = product.id

    i = 1
    while i < 11:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1

    orders = client.get(
        "/orders/?sort_order=asc&offset=2&limit=3"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 3
    assert orders_items[0]["items"][0]["quantity"] == 3
    assert orders_items[1]["items"][0]["quantity"] == 4
    assert orders_items[2]["items"][0]["quantity"] == 5
    
    assert orders_data["total"] == 10
    assert orders_data["offset"] == 2
    assert orders_data["limit"] == 3

def test_get_orders_filter_by_product(
    client,
    create_product
):
    product1 = create_product(stock=100)
    assert product1.id is not None

    i = 1
    while i < 6:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product1.id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1
    
    product2 = create_product(
        sku="TEST-02",
        name="Keyboard-2",
        price=999.9,
        stock=100
    )
    assert product2.id is not None

    i = 1
    while i < 6:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product2.id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1

    orders = client.get(
        f"/orders/?product_id={product2.id}"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 5
    i = 0
    while i < len(orders_items):
        orders_items[i]["items"][0]["product_id"] == product2.id
        i += 1
    
    assert orders_data["total"] == 5
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20


def test_get_orders_filter_by_status(
    client,
    create_product
):
    product1 = create_product(stock=100)
    assert product1.id is not None

    i = 1
    while i < 11:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product1.id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1

    orders = client.get(
        f"/orders/?status=pending"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 10
    i = 0
    while i < len(orders_items):
        orders_items[i]["status"] == "pending"
        i += 1
    
    assert orders_data["total"] == 10
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20

    orders = client.get(
        f"/orders/?status=cancelled"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 0
    assert orders_data["total"] == 0
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20


def test_get_orders_filter_with_pagination(
    client,
    create_product
):
    product1 = create_product(stock=100)
    assert product1.id is not None

    i = 1
    while i < 6:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product1.id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1
    
    product2 = create_product(
        sku="TEST-02",
        name="Keyboard-2",
        price=999.9,
        stock=100
    )
    assert product2.id is not None

    i = 1
    while i < 6:
        order = client.post(
            "/orders/",
            json = {
                "items": [
                    {
                        "product_id": product2.id,
                        "quantity": i
                    }
                ]
            }
        )
        assert order.status_code == 201
        i += 1

    orders = client.get(
        f"/orders/?product_id={product2.id}&limit=3"
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 3
    i = 0
    while i < len(orders_items):
        orders_items[i]["items"][0]["product_id"] == product2.id
        i += 1
    
    assert orders_data["total"] == 5
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 3