import pytest
import uuid

CATALOG_PREFIX = "/api/v1/catalog"
AUTH_PREFIX = "/api/v1/auth"


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


async def create_test_category(aiohttp_client, admin_token: str):
    """Создать тестовую категорию"""
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories",
        json={"name": f"Test Category {uuid4().hex[:8]}"},
        headers=bearer(admin_token)
    )
    assert resp.status == 201
    return await resp.json()


@pytest.mark.asyncio
async def test_get_products_public_ok_200(aiohttp_client):
    resp = await aiohttp_client.get(f"{CATALOG_PREFIX}/products")
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_product_by_id_ok_200(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_get_id_admin", "admin")

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "Test Product for ID",
            "description": "Test description",
            "price": 99.99,
            "rating": 4.5
        },
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201
    product = await resp.json()

    resp = await aiohttp_client.get(f"{CATALOG_PREFIX}/products/{product['id']}")
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert data["id"] == product["id"]
    assert data["name"] == "Test Product for ID"


@pytest.mark.asyncio
async def test_get_product_not_found_404(aiohttp_client):
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    resp = await aiohttp_client.get(f"{CATALOG_PREFIX}/products/{fake_id}")
    assert resp.status == 404, await resp.text()
    data = await resp.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_product_requires_admin_403(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "catalog_create_user")

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "Test Product",
            "price": 100.0
        },
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 403, await resp.text()
    data = await resp.json()
    assert "admin" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_product_admin_ok_201(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_create_admin", "admin")

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "New Product",
            "description": "Product description",
            "price": 199.99,
            "rating": 4.8
        },
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()

    data = await resp.json()
    assert data["name"] == "New Product"
    assert float(data["price"]) == 199.99
    assert data["rating"] == 4.8


@pytest.mark.asyncio
async def test_update_product_admin_ok_200(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_update_admin", "admin")

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "Original Name",
            "price": 100.0
        },
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201
    product = await resp.json()

    resp = await aiohttp_client.put(
        f"{CATALOG_PREFIX}/products/{product['id']}",
        json={
            "name": "Updated Name",
            "price": 150.0
        },
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert data["name"] == "Updated Name"
    assert float(data["price"]) == 150.0


@pytest.mark.asyncio
async def test_delete_product_admin_ok_204(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_delete_admin", "admin")

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": "To Delete",
            "price": 100.0
        },
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201
    product = await resp.json()

    resp = await aiohttp_client.delete(
        f"{CATALOG_PREFIX}/products/{product['id']}",
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 204, await resp.text()

    resp = await aiohttp_client.get(f"{CATALOG_PREFIX}/products/{product['id']}")
    assert resp.status == 404, await resp.text()


@pytest.mark.asyncio
async def test_get_categories_public_ok_200(aiohttp_client):
    resp = await aiohttp_client.get(f"{CATALOG_PREFIX}/categories")
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_category_admin_ok_201(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_cat_admin", "admin")

    unique_name = f"Electronics_{uuid.uuid4().hex[:8]}"

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories",
        json={"name": unique_name},
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()

    data = await resp.json()
    assert data["name"] == unique_name


@pytest.mark.asyncio
async def test_delete_category_with_products_400(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_del_cat_admin", "admin")

    category_name = f"Clothing_{uuid.uuid4().hex[:8]}"

    category_resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories",
        json={"name": category_name},
        headers=bearer(admin_tokens["access_token"])
    )
    assert category_resp.status == 201, f"Category creation failed: {await category_resp.text()}"
    category = await category_resp.json()

    product_name = f"T-Shirt_{uuid.uuid4().hex[:8]}"

    product_resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": product_name,
            "price": 29.99,
            "category_id": category["id"]
        },
        headers=bearer(admin_tokens["access_token"])
    )
    print(f"Product creation: status={product_resp.status}, body={await product_resp.text()}")
    assert product_resp.status == 201, f"Product creation failed: {await product_resp.text()}"

    resp = await aiohttp_client.delete(
        f"{CATALOG_PREFIX}/categories/{category['id']}",
        headers=bearer(admin_tokens["access_token"])
    )
    print(f"Category deletion: status={resp.status}, body={await resp.text()}")

    assert resp.status in (400, 409), f"Expected 400 or 409, got {resp.status}"
    if resp.status in (400, 409):
        data = await resp.json()
        assert any(keyword in data["detail"].lower()
                   for keyword in ["cannot delete", "has products", "already exists", "constraint"])


@pytest.mark.asyncio
async def test_update_category_admin_ok_200(aiohttp_client):
    _, admin_tokens = await register_and_login(aiohttp_client, "catalog_upd_cat_admin", "admin")

    old_name = f"Old_Name_{uuid.uuid4().hex[:8]}"

    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories",
        json={"name": old_name},
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 201, f"Category creation failed: {await resp.text()}"
    category = await resp.json()

    new_name = f"New_Name_{uuid.uuid4().hex[:8]}"

    resp = await aiohttp_client.put(
        f"{CATALOG_PREFIX}/categories/{category['id']}",
        json={"name": new_name},
        headers=bearer(admin_tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert data["name"] == new_name