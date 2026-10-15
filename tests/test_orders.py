
def test_create_order(
    client,
    create_product,
    customer_headers
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
        },
        headers = customer_headers
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
    create_product,
    customer_headers
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
        },
        headers = customer_headers
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
        "/orders/",
        headers = customer_headers
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0

def test_create_order_no_product(
    client,
    customer_headers
):
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
        },
        headers = customer_headers
    )
    
    assert order_response.status_code == 404
    assert order_response.json() == {
        "code": "PRODUCT_NOT_FOUND",
        "detail": f"Product 1 not found" 
    }

    # get orders 判断没有创建order
    get_orders_response = client.get(
        "/orders/",
        headers = customer_headers
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0

def test_create_order_insufficient_stock(
    client,
    create_product,
    customer_headers
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
        },
        headers = customer_headers
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
        "/orders/",
        headers = customer_headers
    )
    orders_info = get_orders_response.json()
    assert len(orders_info["items"]) == 0

def test_get_orders_default_sort_desc(
    client,
    create_product,
    create_order,
    customer_headers
):
    product = create_product()
    assert product.id is not None

    product_id = product.id
    headers = customer_headers

    order1 = create_order(
        items = [
            {
                "product_id": product_id,
                "quantity": 2
            }
        ],
        headers = headers
    )

    order2 = create_order(
        items = [
            {
                "product_id": product_id,
                "quantity": 4
            }
        ],
        headers = headers
    )

    orders = client.get(
        "/orders/",
        headers = headers
    )
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
    create_product,
    create_order,
    customer_headers
):
    product = create_product()
    assert product.id is not None

    product_id = product.id
    headers = customer_headers

    order1 = create_order(
        items = [
            {
                "product_id": product_id,
                "quantity": 2
            }
        ],
        headers = headers
    )

    order2 = create_order(
        items = [
            {
                "product_id": product_id,
                "quantity": 4
            }
        ],
        headers = headers
    )

    orders = client.get(
        "/orders/?sort_order=asc",
        headers = headers
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
    create_product,
    create_order,
    customer_headers
):
    product = create_product(stock=100)
    assert product.id is not None

    product_id = product.id
    headers = customer_headers

    i = 1
    while i < 11:
        order = create_order(
            items = [
                {
                    "product_id": product_id,
                    "quantity": i
                }
            ],
            headers = headers
        )
        i += 1

    orders = client.get(
        "/orders/?sort_order=asc&offset=2&limit=3",
        headers = headers
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
    create_product,
    create_order,
    customer_headers
):
    product1 = create_product(stock=100)
    assert product1.id is not None

    headers = customer_headers

    i = 1
    while i < 6:
        order = create_order(
            items = [
                {
                    "product_id": product1.id,
                    "quantity": i
                }
            ],
            headers = headers
        )
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
        order = create_order(
            items = [
                {
                    "product_id": product2.id,
                    "quantity": i
                }
            ],
            headers = headers
        )
        i += 1

    orders = client.get(
        f"/orders/?product_id={product2.id}",
        headers = headers
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 5

    assert all(
        any(
            item["product_id"] == product2.id
            for item in order["items"]
        )
        for order in orders_items
    )
    
    assert orders_data["total"] == 5
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20


def test_get_orders_filter_by_status(
    client,
    create_product,
    create_order,
    customer_headers
):
    product = create_product(stock=100)
    assert product.id is not None

    headers = customer_headers

    i = 1
    while i < 11:
        order = create_order(
            items = [
                {
                    "product_id": product.id,
                    "quantity": i
                }
            ],
            headers = headers
        )
        i += 1

    orders = client.get(
        f"/orders/?status=pending",
        headers = headers
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 10
    assert all(
        order["status"] == "pending"
        for order in orders_items
    )

    assert orders_data["total"] == 10
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 20

    orders = client.get(
        f"/orders/?status=cancelled",
        headers = headers
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
    create_product,
    create_order,
    customer_headers
):
    product1 = create_product(stock=100)
    assert product1.id is not None

    headers = customer_headers

    i = 1
    while i < 6:
        order = create_order(
            items = [
                {
                    "product_id": product1.id,
                    "quantity": i
                }
            ],
            headers = headers
        )
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
        order = create_order(
            items = [
                {
                    "product_id": product2.id,
                    "quantity": i
                }
            ],
            headers = headers
        )
        i += 1

    orders = client.get(
        f"/orders/?product_id={product2.id}&limit=3",
        headers = headers
    )
    assert orders.status_code == 200

    orders_data = orders.json()
    orders_items = orders_data["items"]
    assert len(orders_items) == 3
    assert all(
        any(
            item["product_id"] == product2.id
            for item in order["items"]
        )
        for order in orders_items
    )
    
    assert orders_data["total"] == 5
    assert orders_data["offset"] == 0
    assert orders_data["limit"] == 3

def test_get_orders_invalid_sort_order(
    client,
    customer_headers
):
    response = client.get(
        "/orders/?sort_order=random",
        headers = customer_headers
    )

    assert response.status_code == 422

def test_get_orders_invalid_pagination(
    client,
    customer_headers
):
    headers = customer_headers

    response = client.get(
        "/orders/?offset=-1",
        headers = headers
    )

    assert response.status_code == 422

    response = client.get(
        "/orders/?limit=0",
        headers = headers
    )

    assert response.status_code == 422

    response = client.get(
        "/orders/?limit=101",
        headers = headers
    )

    assert response.status_code == 422

def test_get_orders_ownership(
    client,
    create_product,
    create_order,
    create_auth_user
):
    product = create_product(stock=100)
    assert product.id is not None

    product_id = product.id
    user1, headers1 = create_auth_user(
        username = "user1"
    )

    i = 1
    while i < 4:
        order = create_order(
            items = [
                {
                    "product_id": product_id,
                    "quantity": i
                }
            ],
            headers = headers1
        )
        i += 1

    user2, headers2 = create_auth_user(
        username = "user2"
    )
    while i < 7:
        order = create_order(
            items = [
                {
                    "product_id": product_id,
                    "quantity": i
                }
            ],
            headers = headers2
        )
        i += 1

    user1_orders = client.get(
        "/orders/?sort_order=asc",
        headers = headers1
    )
    assert user1_orders.status_code == 200

    user1_orders_data = user1_orders.json()
    user1_orders_items = user1_orders_data["items"]
    assert len(user1_orders_items) == 3
    assert user1_orders_items[0]["items"][0]["quantity"] == 1
    assert user1_orders_items[1]["items"][0]["quantity"] == 2
    assert user1_orders_items[2]["items"][0]["quantity"] == 3
    
    assert user1_orders_data["total"] == 3
    assert user1_orders_data["offset"] == 0
    assert user1_orders_data["limit"] == 20

    user2_orders = client.get(
        "/orders/?sort_order=asc",
        headers = headers2
    )
    assert user2_orders.status_code == 200

    user2_orders_data = user2_orders.json()
    user2_orders_items = user2_orders_data["items"]
    assert len(user2_orders_items) == 3
    assert user2_orders_items[0]["items"][0]["quantity"] == 4
    assert user2_orders_items[1]["items"][0]["quantity"] == 5
    assert user2_orders_items[2]["items"][0]["quantity"] == 6
    
    assert user2_orders_data["total"] == 3
    assert user2_orders_data["offset"] == 0
    assert user2_orders_data["limit"] == 20