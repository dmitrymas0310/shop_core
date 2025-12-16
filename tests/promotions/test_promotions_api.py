import pytest
from datetime import datetime, timedelta

# Префиксы API
AUTH_PREFIX = "/api/v1/auth"
USERS_PREFIX = "/api/v1/users"
CATALOG_PREFIX = "/api/v1/catalog"
PROMOTIONS_PREFIX = "/api/v1/promotions"


def bearer(token: str) -> dict:
    """Создает заголовок авторизации."""
    return {"Authorization": f"Bearer {token}"}


# --- Вспомогательные функции для тестов ---

async def register_user(aiohttp_client, login: str, role: str = "user", password: str = "StrongPass123!"):
    """Регистрирует пользователя через API."""
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
    """Выполняет вход и возвращает токены."""
    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={"login": login, "password": password})
    assert resp.status == 200, await resp.text()
    return await resp.json()


async def create_product(aiohttp_client, admin_token: str, name: str, price: float = 100.0):
    """Создает товар через API."""
    resp = await aiohttp_client.post(
        f"{CATALOG_PREFIX}/admin/products",
        json={"name": name, "description": "Test description", "price": price},
        headers=bearer(admin_token)
    )
    assert resp.status == 201, await resp.text()
    return await resp.json()


async def create_promotion(aiohttp_client, admin_token: str, title: str, discount: float = 10.0):
    """Создает акцию через API."""
    starts_at = datetime.utcnow().isoformat()
    ends_at = (datetime.utcnow() + timedelta(days=10)).isoformat()
    
    resp = await aiohttp_client.post(
        f"{PROMOTIONS_PREFIX}/admin",
        json={
            "title": title,
            "description": "Test promotion",
            "discount_percent": discount,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "is_active": True
        },
        headers=bearer(admin_token)
    )
    assert resp.status == 201, await resp.text()
    return await resp.json()


# --- Тесты для Promotions ---

@pytest.mark.asyncio
async def test_create_promotion_as_admin_ok_201(aiohttp_client):
    """[Admin] Успешное создание акции."""
    await register_user(aiohttp_client, "promo_admin", role="admin")
    tokens = await login(aiohttp_client, "promo_admin")
    
    promo = await create_promotion(aiohttp_client, tokens["access_token"], "New Year Sale")
    
    assert "id" in promo
    assert promo["title"] == "New Year Sale"
    assert promo["discount_percent"] == 10.0


@pytest.mark.asyncio
async def test_create_promotion_as_user_forbidden_403(aiohttp_client):
    """[User] Попытка создать акцию обычным пользователем."""
    await register_user(aiohttp_client, "promo_user", role="user")
    tokens = await login(aiohttp_client, "promo_user")
    
    starts_at = datetime.utcnow().isoformat()
    ends_at = (datetime.utcnow() + timedelta(days=10)).isoformat()
    
    resp = await aiohttp_client.post(
        f"{PROMOTIONS_PREFIX}/admin",
        json={
            "title": "User Promo",
            "discount_percent": 15,
            "starts_at": starts_at,
            "ends_at": ends_at
        },
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 403, await resp.text()


@pytest.mark.asyncio
async def test_get_active_promotions_public_ok_200(aiohttp_client):
    """[Public] Получение списка активных акций."""
    await register_user(aiohttp_client, "promo_admin_2", role="admin")
    tokens = await login(aiohttp_client, "promo_admin_2")
    
    await create_promotion(aiohttp_client, tokens["access_token"], "Active Promo")
    
    resp = await aiohttp_client.get(f"{PROMOTIONS_PREFIX}/")
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["title"] == "Active Promo"


@pytest.mark.asyncio
async def test_get_promotion_by_id_public_ok_200(aiohttp_client):
    """[Public] Получение акции по ID."""
    await register_user(aiohttp_client, "promo_admin_3", role="admin")
    tokens = await login(aiohttp_client, "promo_admin_3")
    
    promo = await create_promotion(aiohttp_client, tokens["access_token"], "Promo By ID")
    
    resp = await aiohttp_client.get(f"{PROMOTIONS_PREFIX}/{promo['id']}")
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert data["id"] == promo["id"]
    assert data["title"] == "Promo By ID"


@pytest.mark.asyncio
async def test_attach_product_to_promotion_ok_200(aiohttp_client):
    """[Admin] Привязка товара к акции."""
    await register_user(aiohttp_client, "promo_admin_4", role="admin")
    tokens = await login(aiohttp_client, "promo_admin_4")
    
    product = await create_product(aiohttp_client, tokens["access_token"], "Super TV")
    promo = await create_promotion(aiohttp_client, tokens["access_token"], "TV Sale")
    
    resp = await aiohttp_client.post(
        f"{PROMOTIONS_PREFIX}/admin/{promo['id']}/products",
        json={"product_ids": [product["id"]]},
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    
    assert "product_ids" in data
    assert product["id"] in data["product_ids"]


@pytest.mark.asyncio
async def test_detach_product_from_promotion_ok_200(aiohttp_client):
    """[Admin] Отвязка товара от акции."""
    await register_user(aiohttp_client, "promo_admin_5", role="admin")
    tokens = await login(aiohttp_client, "promo_admin_5")
    
    product = await create_product(aiohttp_client, tokens["access_token"], "Mega Phone")
    promo = await create_promotion(aiohttp_client, tokens["access_token"], "Phone Sale")
    
    # Привязываем
    await aiohttp_client.post(
        f"{PROMOTIONS_PREFIX}/admin/{promo['id']}/products",
        json={"product_ids": [product["id"]]},
        headers=bearer(tokens["access_token"])
    )
    
    # Отвязываем
    resp = await aiohttp_client.delete(
        f"{PROMOTIONS_PREFIX}/admin/{promo['id']}/products",
        json={"product_ids": [product["id"]]},
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    
    assert "product_ids" in data
    assert product["id"] not in data["product_ids"]


@pytest.mark.asyncio
async def test_delete_promotion_as_admin_ok_200(aiohttp_client):
    """[Admin] Удаление акции."""
    await register_user(aiohttp_client, "promo_admin_6", role="admin")
    tokens = await login(aiohttp_client, "promo_admin_6")
    
    promo = await create_promotion(aiohttp_client, tokens["access_token"], "To Be Deleted")
    
    resp = await aiohttp_client.delete(
        f"{PROMOTIONS_PREFIX}/admin/{promo['id']}",
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()
    
    # Проверяем, что акция удалена
    get_resp = await aiohttp_client.get(f"{PROMOTIONS_PREFIX}/{promo['id']}")
    assert get_resp.status == 404, await get_resp.text()
