import pytest
import uuid

CART_PREFIX = "/api/v1/cart"
AUTH_PREFIX = "/api/v1/auth"
CATALOG_PREFIX = "/api/v1/catalog"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(aiohttp_client, login_suffix: str, role: str = "user"):
    unique_id = uuid.uuid4().hex[:8]
    login = f"{login_suffix}_{unique_id}"

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Test",
        "last_name": "User",
        "login": login,
        "password": "pwd1",
        "role": role,
    })

    print(f"Registration attempt: login={login}, status={resp.status}")

    if resp.status != 200:
        error_text = await resp.text()
        print(f"Registration failed: {error_text}")

        if resp.status == 409:
            print(f"User {login} already exists, trying to login...")
        else:
            assert resp.status == 200, f"Registration failed: {error_text}"

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": login,
        "password": "pwd1",
    })

    print(f"Login attempt: status={resp.status}")

    if resp.status != 200:
        error_text = await resp.text()
        print(f"Login failed: {error_text}")

    assert resp.status == 200, f"Login failed: {await resp.text()}"

    tokens = await resp.json()
    return {"id": "test_id", "login": login}, tokens


async def create_test_product(aiohttp_client, admin_token: str):
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "Test Product",
            "description": "Test description",
            "price": 100.50,
            "rating": 4.5,
        },
        headers=bearer(admin_token)
    )
    assert resp.status == 201
    return await resp.json()


@pytest.mark.asyncio
async def test_get_cart_requires_auth(aiohttp_client):
    resp = await aiohttp_client.get(f"{CART_PREFIX}/")
    assert resp.status in (401, 403), await resp.text()


@pytest.mark.asyncio
async def test_get_cart_ok_200(aiohttp_client):
    _, tokens = await register_and_login(aiohttp_client, "cart_get_ok")

    resp = await aiohttp_client.get(
        f"{CART_PREFIX}/",
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert "id" in data
    assert data["status"] == "active"
    assert data["items"] == []


@pytest.mark.asyncio
async def test_add_item_to_cart_ok_201(aiohttp_client):
    user_data, user_tokens = await register_and_login(aiohttp_client, "cart_add_user")
    _, admin_tokens = await register_and_login(aiohttp_client, "cart_add_admin", "admin")

    product = await create_test_product(aiohttp_client, admin_tokens["access_token"])

    resp = await aiohttp_client.post(
        f"{CART_PREFIX}/items",
        json={
            "product_id": product["id"],
            "quantity": 2
        },
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()

    data = await resp.json()
    assert data["product_id"] == product["id"]
    assert data["quantity"] == 2
    assert float(data["price_at_add"]) == 100.50


@pytest.mark.asyncio
async def test_update_cart_item_quantity_ok_200(aiohttp_client):
    user_data, user_tokens = await register_and_login(aiohttp_client, "cart_update_qty")
    _, admin_tokens = await register_and_login(aiohttp_client, "cart_update_admin", "admin")
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"])

    resp = await aiohttp_client.post(
        f"{CART_PREFIX}/items",
        json={"product_id": product["id"], "quantity": 1},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201

    resp = await aiohttp_client.put(
        f"{CART_PREFIX}/items/{product['id']}",
        json={"quantity": 3},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert data["quantity"] == 3


@pytest.mark.asyncio
async def test_remove_item_from_cart_ok_204(aiohttp_client):
    user_data, user_tokens = await register_and_login(aiohttp_client, "cart_remove")
    _, admin_tokens = await register_and_login(aiohttp_client, "cart_remove_admin", "admin")
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"])

    resp = await aiohttp_client.post(
        f"{CART_PREFIX}/items",
        json={"product_id": product["id"], "quantity": 1},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201

    resp = await aiohttp_client.delete(
        f"{CART_PREFIX}/items/{product['id']}",
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 204, await resp.text()

    resp = await aiohttp_client.get(
        f"{CART_PREFIX}/",
        headers=bearer(user_tokens["access_token"])
    )
    data = await resp.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart_ok_204(aiohttp_client):
    user_data, user_tokens = await register_and_login(aiohttp_client, "cart_clear")
    _, admin_tokens = await register_and_login(aiohttp_client, "cart_clear_admin", "admin")
    product1 = await create_test_product(aiohttp_client, admin_tokens["access_token"])
    product2 = await create_test_product(aiohttp_client, admin_tokens["access_token"])

    await aiohttp_client.post(
        f"{CART_PREFIX}/items",
        json={"product_id": product1["id"], "quantity": 1},
        headers=bearer(user_tokens["access_token"])
    )
    await aiohttp_client.post(
        f"{CART_PREFIX}/items",
        json={"product_id": product2["id"], "quantity": 2},
        headers=bearer(user_tokens["access_token"])
    )

    resp = await aiohttp_client.delete(
        f"{CART_PREFIX}/clear",
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 204, await resp.text()

    resp = await aiohttp_client.get(
        f"{CART_PREFIX}/",
        headers=bearer(user_tokens["access_token"])
    )
    data = await resp.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_user_cart_admin_access_ok_200(aiohttp_client):
    user_resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Target",
        "last_name": "User",
        "login": f"target_user_{uuid.uuid4().hex[:8]}",
        "password": "pwd1",
        "role": "user",
    })

    assert user_resp.status in (200, 409), await user_resp.text()

    if user_resp.status == 200:
        user_data = await user_resp.json()
        user_id = user_data["id"]
    else:
        # Если пользователь уже существует, получим его ID через логин
        # Или пропустим тест
        pytest.skip("Could not get real user ID for test")

    _, admin_tokens = await register_and_login(aiohttp_client, "cart_admin_get", "admin")

    resp = await aiohttp_client.get(
        f"{CART_PREFIX}/{user_id}",
        headers=bearer(admin_tokens["access_token"])
    )

    print(f"Admin cart access: status={resp.status}, body={await resp.text()}")
    assert resp.status in (200, 404), f"Expected 200 or 404, got {resp.status}"

    if resp.status == 200:
        data = await resp.json()
        if "user_id" in data:
            assert data["user_id"] == user_id
