
def test_admin_get_all_orders(
    client,
    create_product,
    create_auth_user,
    create_order
):
    product = create_product(stock=100)
    assert product.id is not None

    product_id = product.id

    user1, headers1 = create_auth_user(
        username = "customer_user1",
        role = "customer"
    )
    i = 1
    while i < 6:
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
        username = "customer_user2",
        role = "customer"
    )

    while i < 11:
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
        "/orders/",
        headers = headers1
    )
    assert user1_orders.status_code == 200

    user1_orders_data = user1_orders.json()
    user1_orders_items = user1_orders_data["items"]
    assert len(user1_orders_items) == 5

    user2_orders = client.get(
        "/orders/",
        headers = headers2
    )
    assert user2_orders.status_code == 200

    user2_orders_data = user2_orders.json()
    user2_orders_items = user2_orders_data["items"]
    assert len(user2_orders_items) == 5

    admin, admin_headers = create_auth_user(
        username = "admin_user",
        role = "admin"
    )
    admin_orders = client.get(
        "/admin/orders/",
        headers = admin_headers
    )
    assert admin_orders.status_code == 200

    admin_orders_data = admin_orders.json()
    admin_orders_items = admin_orders_data["items"]
    assert len(admin_orders_items) == 10

    user2_admin_orders_response = client.get(
        "/admin/orders/",
        headers = headers2
    )
    assert user2_admin_orders_response.status_code == 403
    assert user2_admin_orders_response.json() == {
        "code": "FORBIDDEN",
        "detail": "Insufficient permissions"
    }

def test_admin_get_others_order(
    client,
    create_product,
    create_auth_user,
    create_order
):
    product = create_product(stock=100)
    assert product.id is not None

    product_id = product.id

    user1, headers1 = create_auth_user(
        username = "customer_user1",
        role = "customer"
    )

    order = create_order(
        items = [
            {
                "product_id": product_id,
                "quantity": 10
            }
        ],
        headers = headers1
    )
    assert isinstance(order["id"], int) 
    
    user2, headers2 = create_auth_user(
        username = "customer_user2",
        role = "customer"
    )

    admin, admin_headers = create_auth_user(
        username = "admin_user",
        role = "admin"
    )

    admin_order = client.get(
        f"/admin/orders/{order["id"]}",
        headers = admin_headers
    )
    assert admin_order.status_code == 200

    order_data = admin_order.json()
    assert order_data["id"] == order["id"]
    assert order_data["user_id"] == user1.id
    
    user2_get_admin_order_response = client.get(
        f"/admin/orders/{order["id"]}",
        headers = headers2
    )
    assert user2_get_admin_order_response.status_code == 403
    assert user2_get_admin_order_response.json() == {
        "code": "FORBIDDEN",
        "detail": "Insufficient permissions"
    }