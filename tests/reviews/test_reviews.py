import pytest

USERS_PREFIX = "/api/v1/users"
AUTH_PREFIX = "/api/v1/auth"
CATALOG_PREFIX = "/api/v1/catalog"
REVIEWS_PREFIX = "/api/v1/reviews"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def register_user(aiohttp_client, login: str, role: str = "user", password: str = "StrongPass123!"):
    resp = await aiohttp_client.post(f"{USERS_PREFIX}/", json={
        "first_name": "Test",
        "last_name": "User",
        "login": login,
        "password": password,
        "role": role,
    })
    assert resp.status == 201, await resp.text()
    return await resp.json()


async def login(aiohttp_client, login: str, password: str = "StrongPass123!"):
    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={"login": login, "password": password})
    assert resp.status == 200, await resp.text()
    return await resp.json()


async def create_category_as_admin(aiohttp_client, admin_token: str, name: str = "Electronics"):
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/categories/",
        json={"name": name},
        headers=bearer(admin_token)
    )
    assert resp.status == 201, await resp.text()
    return await resp.json()


async def create_product_as_admin(aiohttp_client, admin_token: str, category_id: str, name: str = "Laptop"):
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/products/",
        json={
            "name": name,
            "description": "Test product",
            "price": "999.99",
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
    user = await register_user(aiohttp_client, "reviewer")
    user_tokens = await login(aiohttp_client, "reviewer")

    admin = await register_user(aiohttp_client, "review_admin", role="admin")
    admin_tokens = await login(aiohttp_client, "review_admin")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={
            "product_id": product["id"],
            "rating": 4.5,
            "comment": "Great product!"
        },
        headers=bearer(user_tokens["access_token"])
    )
    assert resp.status == 201, await resp.text()
    data = await resp.json()
    assert "id" in data
    assert data["rating"] == 4.5
    assert data["product_id"] == product["id"]
    assert data["user_id"] == user["id"]


@pytest.mark.asyncio
async def test_create_review_unauthorized_401(aiohttp_client):
    # Без токена
    resp = await aiohttp_client.post(f"{REVIEWS_PREFIX}/", json={
        "product_id": "123e4567-e89b-12d3-a456-426614174000",
        "rating": 3.0
    })
    assert resp.status == 401, await resp.text()


@pytest.mark.asyncio
async def test_create_review_invalid_rating_too_low_422(aiohttp_client):
    user = await register_user(aiohttp_client, "reviewer_low")
    tokens = await login(aiohttp_client, "reviewer_low")

    admin = await register_user(aiohttp_client, "admin_low", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_low")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 0.5},
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_create_review_invalid_rating_too_high_422(aiohttp_client):
    user = await register_user(aiohttp_client, "reviewer_high")
    tokens = await login(aiohttp_client, "reviewer_high")

    admin = await register_user(aiohttp_client, "admin_high", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_high")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.5},
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_get_review_by_id_ok_200(aiohttp_client):
    user = await register_user(aiohttp_client, "reader")
    tokens = await login(aiohttp_client, "reader")

    admin = await register_user(aiohttp_client, "admin_reader", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_reader")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.0, "comment": "Perfect!"},
        headers=bearer(tokens["access_token"])
    )
    review = await resp.json()

    resp2 = await aiohttp_client.get(f"{REVIEWS_PREFIX}/{review['id']}")
    assert resp2.status == 200, await resp2.text()
    data = await resp2.json()
    assert data["id"] == review["id"]
    assert data["comment"] == "Perfect!"


@pytest.mark.asyncio
async def test_get_reviews_by_product_ok_200(aiohttp_client):
    user = await register_user(aiohttp_client, "reviewer_list")
    tokens = await login(aiohttp_client, "reviewer_list")

    admin = await register_user(aiohttp_client, "admin_list", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_list")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    await aiohttp_client.post(f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(tokens["access_token"])
    )
    await aiohttp_client.post(f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 2.0, "comment": "Not good"},
        headers=bearer(tokens["access_token"])
    )

    resp = await aiohttp_client.get(f"{REVIEWS_PREFIX}/product/{product['id']}")
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert len(data) == 2
    ratings = {r["rating"] for r in data}
    assert ratings == {4.0, 2.0}


@pytest.mark.asyncio
async def test_update_review_author_ok_200(aiohttp_client):
    user = await register_user(aiohttp_client, "updater")
    tokens = await login(aiohttp_client, "updater")

    admin = await register_user(aiohttp_client, "admin_upd", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_upd")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 3.0},
        headers=bearer(tokens["access_token"])
    )
    review = await resp.json()

    resp2 = await aiohttp_client.put(
        f"{REVIEWS_PREFIX}/{review['id']}",
        json={"rating": 5.0, "comment": "Changed my mind!"},
        headers=bearer(tokens["access_token"])
    )
    assert resp2.status == 200, await resp2.text()
    updated = await resp2.json()
    assert updated["rating"] == 5.0
    assert updated["comment"] == "Changed my mind!"


@pytest.mark.asyncio
async def test_update_review_other_user_forbidden_403(aiohttp_client):
    user_a = await register_user(aiohttp_client, "author")
    tokens_a = await login(aiohttp_client, "author")

    user_b = await register_user(aiohttp_client, "intruder")
    tokens_b = await login(aiohttp_client, "intruder")

    admin = await register_user(aiohttp_client, "admin_upd2", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_upd2")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(tokens_a["access_token"])
    )
    review = await resp.json()

    resp2 = await aiohttp_client.put(
        f"{REVIEWS_PREFIX}/{review['id']}",
        json={"rating": 1.0},
        headers=bearer(tokens_b["access_token"])
    )
    assert resp2.status == 403, await resp2.text()


@pytest.mark.asyncio
async def test_delete_review_author_ok_204(aiohttp_client):
    user = await register_user(aiohttp_client, "deleter")
    tokens = await login(aiohttp_client, "deleter")

    admin = await register_user(aiohttp_client, "admin_del", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_del")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 4.0},
        headers=bearer(tokens["access_token"])
    )
    review = await resp.json()

    resp2 = await aiohttp_client.delete(
        f"{REVIEWS_PREFIX}/{review['id']}",
        headers=bearer(tokens["access_token"])
    )
    assert resp2.status == 204

    # Проверяем, что отзыв удалён
    resp3 = await aiohttp_client.get(f"{REVIEWS_PREFIX}/{review['id']}")
    assert resp3.status == 404, await resp3.text()


@pytest.mark.asyncio
async def test_delete_review_other_user_forbidden_403(aiohttp_client):
    user_a = await register_user(aiohttp_client, "owner")
    tokens_a = await login(aiohttp_client, "owner")

    user_b = await register_user(aiohttp_client, "intruder2")
    tokens_b = await login(aiohttp_client, "intruder2")

    admin = await register_user(aiohttp_client, "admin_del2", role="admin")
    admin_tokens = await login(aiohttp_client, "admin_del2")
    category = await create_category_as_admin(aiohttp_client, admin_tokens["access_token"])
    product = await create_product_as_admin(aiohttp_client, admin_tokens["access_token"], category["id"])

    resp = await aiohttp_client.post(
        f"{REVIEWS_PREFIX}/",
        json={"product_id": product["id"], "rating": 5.0},
        headers=bearer(tokens_a["access_token"])
    )
    review = await resp.json()

    resp2 = await aiohttp_client.delete(
        f"{REVIEWS_PREFIX}/{review['id']}",
        headers=bearer(tokens_b["access_token"])
    )
    assert resp2.status == 403, await resp2.text()