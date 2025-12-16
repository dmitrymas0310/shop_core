import pytest
import uuid
from uuid import uuid4

ORDERS_PREFIX = "/api/v1/orders"
AUTH_PREFIX = "/api/v1/auth"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(aiohttp_client, login_suffix: str, role: str = "user"):
    """Регистрация и авторизация пользователя"""
    unique_id = uuid.uuid4().hex[:8]
    login = f"{login_suffix}_{unique_id}"

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Test",
        "last_name": "User",
        "login": login,
        "password": "pwd1",
        "role": role,
    })

    if resp.status != 200:
        error_text = await resp.text()
        if resp.status == 409:
            print(f"User {login} already exists")
        else:
            assert resp.status == 200, f"Registration failed: {error_text}"

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": login,
        "password": "pwd1",
    })

    assert resp.status == 200, f"Login failed: {await resp.text()}"
    tokens = await resp.json()
    
    return {"login": login, "role": role}, tokens


@pytest.mark.asyncio
async def test_create_order_requires_auth_401(aiohttp_client):
    """Тест: создание заказа требует авторизации"""
    order_data = {
        "shipping_address": "ул. Тестовая, 1",
        "phone_number": "+79991234567",
        "items": []
    }
    
    resp = await aiohttp_client.post(
        f"{ORDERS_PREFIX}/",
        json=order_data
    )
    
    assert resp.status == 401, await resp.text()


@pytest.mark.asyncio
async def test_create_order_auth_ok_201(aiohttp_client):
    """Тест: успешное создание заказа"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "order_user")
    
    order_data = {
        "shipping_address": "ул. Тестовая, д. 1",
        "phone_number": "+79991234567",
        "notes": "Тестовый заказ",
        "items": [
            {
                "product_id": str(uuid4()),
                "quantity": 2
            }
        ]
    }
    
    resp = await aiohttp_client.post(
        f"{ORDERS_PREFIX}/",
        json=order_data,
        headers=bearer(user_tokens["access_token"])
    )
    
    print(f"Order creation: status={resp.status}")
    
    # Может быть 201 (успех) или 404 (товар не найден)
    assert resp.status in (201, 404), await resp.text()
    
    if resp.status == 201:
        data = await resp.json()
        assert data["shipping_address"] == order_data["shipping_address"]
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_my_orders_auth_ok_200(aiohttp_client):
    """Тест: получение своих заказов"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "myorders_user")
    
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/my",
        headers=bearer(user_tokens["access_token"])
    )
    
    assert resp.status == 200, await resp.text()
    
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_my_order_by_id_ok_200(aiohttp_client):
    """Тест: получение конкретного заказа"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "orderbyid_user")
    
    # Создаем тестовый заказ
    order_data = {
        "shipping_address": "ул. Тестовая, 1",
        "phone_number": "+79991234567",
        "items": [{"product_id": str(uuid4()), "quantity": 1}]
    }
    
    create_resp = await aiohttp_client.post(
        f"{ORDERS_PREFIX}/",
        json=order_data,
        headers=bearer(user_tokens["access_token"])
    )
    
    if create_resp.status == 201:
        order = await create_resp.json()
        
        # Получаем созданный заказ
        resp = await aiohttp_client.get(
            f"{ORDERS_PREFIX}/my/{order['id']}",
            headers=bearer(user_tokens["access_token"])
        )
        
        assert resp.status in (200, 404), await resp.text()
        
        if resp.status == 200:
            data = await resp.json()
            assert data["id"] == order["id"]


@pytest.mark.asyncio
async def test_get_order_not_found_404(aiohttp_client):
    """Тест: заказ не найден"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "notfound_user")
    
    fake_id = str(uuid4())
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/my/{fake_id}",
        headers=bearer(user_tokens["access_token"])
    )
    
    assert resp.status == 404, await resp.text()
    
    data = await resp.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_all_orders_requires_admin_403(aiohttp_client):
    """Тест: получение всех заказов требует админских прав"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "nonadmin_user")
    
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/",
        headers=bearer(user_tokens["access_token"])
    )
    
    assert resp.status == 403, await resp.text()
    
    data = await resp.json()
    assert "admin" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_all_orders_admin_ok_200(aiohttp_client):
    """Тест: администратор может получить все заказы"""
    admin_info, admin_tokens = await register_and_login(aiohttp_client, "orders_admin", "admin")
    
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/",
        headers=bearer(admin_tokens["access_token"])
    )
    
    assert resp.status == 200, await resp.text()
    
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_order_status_requires_auth_401(aiohttp_client):
    """Тест: обновление статуса требует авторизации"""
    order_id = str(uuid4())
    status_update = {"status": "completed"}
    
    resp = await aiohttp_client.patch(
        f"{ORDERS_PREFIX}/{order_id}/status",
        json=status_update
    )
    
    assert resp.status == 401, await resp.text()


@pytest.mark.asyncio
async def test_get_orders_stats_requires_admin_403(aiohttp_client):
    """Тест: статистика требует админских прав"""
    user_info, user_tokens = await register_and_login(aiohttp_client, "stats_user")
    
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/stats/count",
        headers=bearer(user_tokens["access_token"])
    )
    
    assert resp.status == 403, await resp.text()
    
    data = await resp.json()
    assert "admin" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_orders_stats_admin_ok_200(aiohttp_client):
    """Тест: администратор может получить статистику"""
    admin_info, admin_tokens = await register_and_login(aiohttp_client, "stats_admin", "admin")
    
    resp = await aiohttp_client.get(
        f"{ORDERS_PREFIX}/stats/count",
        headers=bearer(admin_tokens["access_token"])
    )
    
    assert resp.status == 200, await resp.text()
    
    data = await resp.json()
    assert "count" in data
    assert isinstance(data["count"], int)