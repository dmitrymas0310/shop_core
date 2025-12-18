import pytest
import uuid

AUTH_PREFIX = "/api/v1/auth"
CATALOG_PREFIX = "/api/v1/catalog"
REVIEWS_PREFIX = "/api/v1/reviews"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(aiohttp_client, login_suffix: str, role: str = "user"):
    """Регистрация и логин с уникальным логином (UUID-based)"""
    login = f"{login_suffix}_{uuid.uuid4().hex[:8]}"
    password = "pwd1"

    # Регистрация
    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Test",
        "last_name": "User",
        "login": login,
        "password": password,
        "role": role,
    })
    assert resp.status == 200, f"Registration failed: {await resp.text()}"

    # Логин
    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": login,
        "password": password,
    })
    assert resp.status == 200, f"Login failed: {await resp.text()}"

    tokens = await resp.json()
    return {"login": login}, tokens


async def create_test_category(aiohttp_client, admin_token: str):
    """Создать уникальную категорию"""
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories",
        json={"name": f"Category_{uuid.uuid4().hex[:8]}"},
        headers=bearer(admin_token)
    )
    assert resp.status == 201, await resp.text()
    return await resp.json()


async def create_test_product(aiohttp_client, admin_token: str, category_id: str):
    """Создать товар с UUID-совместимым category_id"""
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": f"Product_{uuid.uuid4().hex[:8]}",
            "description": "Test product",
            "price": "99.99",
            "category_id": category_id  
        },
        headers=bearer(admin_token)
    )
    assert resp.status == 201, await resp.text()
    return await resp.json()


# --------------------------
# ТЕСТЫ
# --------------------------

@pytest.mark.asyncio
async def test_create_review_ok_201(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "reviewer")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_rev", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={
            "product_id": product["id"], 
            "rating": 4.5,
            "comment": "Great!"
        },
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()


@pytest.mark.asyncio
async def test_create_review_unauthorized_401(aiohttp_client):
    resp = await aiohttp_client.post(f"{REVIEWS_PREFIX}/", json={
        "product_id": str(uuid.uuid4()),
        "rating": 3.0
    })
    assert resp.status == 403
    data = await resp.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_review_invalid_rating_too_low_422(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "low")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_low", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 0.5},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_create_review_invalid_rating_too_high_422(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "high")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_high", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.5},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_get_review_by_id_ok_200(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "reader")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_reader", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.0},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    review = await resp.json()

    resp2 = await aiohttp_client.get(f"{REVIEWS_PREFIX}/{review['id']}")
    assert resp2.status == 200, await resp2.text()


@pytest.mark.asyncio
async def test_get_reviews_by_product_ok_200(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "list")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_list", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    await aiohttp_client.post(f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(user_tokens["access_token"])
    )
    await aiohttp_client.post(f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 2.0},
        headers=bearer(user_tokens["access_token"])
    )

    resp = await aiohttp_client.get(f"{REVIEWS_PREFIX}/product/{product['id']}")
    assert resp.status == 200, await resp.text()


@pytest.mark.asyncio
async def test_update_review_author_ok_200(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "updater")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_upd", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 3.0},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    review = await resp.json()

    resp2 = await aiohttp_client.put(
        f"{REVIEWS_PREFIX}/{review['id']}",
        json={"rating": 5.0, "comment": "Updated!"},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp2.status == 200, await resp2.text()


@pytest.mark.asyncio
async def test_update_review_other_user_forbidden_403(aiohttp_client):
    _, user_a_tokens = await register_and_login(aiohttp_client, "author")
    _, user_b_tokens = await register_and_login(aiohttp_client, "intruder")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_upd2", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(user_a_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    review = await resp.json()

    resp2 = await aiohttp_client.put(
        f"{REVIEWS_PREFIX}/{review['id']}",
        json={"rating": 1.0},
        headers=bearer(user_b_tokens["access_token"])
    )
    assert resp2.status == 403, await resp2.text()


@pytest.mark.asyncio
async def test_delete_review_author_ok_204(aiohttp_client):
    _, user_tokens = await register_and_login(aiohttp_client, "deleter")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_del", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    review = await resp.json()

    resp2 = await aiohttp_client.delete(
        f"{REVIEWS_PREFIX}/{review['id']}",
        headers=bearer(user_tokens["access_token"])
    )
    assert resp2.status == 204


@pytest.mark.asyncio
async def test_delete_review_other_user_forbidden_403(aiohttp_client):
    _, user_a_tokens = await register_and_login(aiohttp_client, "owner")
    _, user_b_tokens = await register_and_login(aiohttp_client, "intruder2")
    _, admin_tokens = await register_and_login(aiohttp_client, "admin_del2", "admin")

    category = await create_test_category(aiohttp_client, admin_tokens["access_token"])
    product = await create_test_product(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.0},
        headers=bearer(user_a_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    review = await resp.json()

    resp2 = await aiohttp_client.delete(
        f"{REVIEWS_PREFIX}/{review['id']}",
        headers=bearer(user_b_tokens["access_token"])
    )
    assert resp2.status == 403, await resp2.text()