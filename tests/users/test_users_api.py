import pytest

USERS_PREFIX = "/api/v1/users"
AUTH_PREFIX = "/api/v1/auth"


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


@pytest.mark.asyncio
async def test_users_register_ok_201(aiohttp_client):
    data = await register_user(aiohttp_client, "users_reg_ok")
    assert "id" in data
    assert data["login"] == "users_reg_ok"


@pytest.mark.asyncio
async def test_users_register_validation_422(aiohttp_client):
    resp = await aiohttp_client.post(f"{USERS_PREFIX}/", json={
        "first_name": "Test",
        "login": "users_reg_422",
        "password": "StrongPass123!",
        "role": "USER",
    })
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_users_list_requires_auth(aiohttp_client):
    resp = await aiohttp_client.get(f"{USERS_PREFIX}/")
    assert resp.status in (401, 403), await resp.text()


@pytest.mark.asyncio
async def test_users_list_forbidden_for_user_403(aiohttp_client):
    await register_user(aiohttp_client, "list_user")
    tokens = await login(aiohttp_client, "list_user")

    resp = await aiohttp_client.get(f"{USERS_PREFIX}/", headers=bearer(tokens["access_token"]))
    assert resp.status == 403, await resp.text()


@pytest.mark.asyncio
async def test_users_list_admin_ok_200(aiohttp_client):
    await register_user(aiohttp_client, "list_admin", role="admin")
    tokens = await login(aiohttp_client, "list_admin")

    resp = await aiohttp_client.get(f"{USERS_PREFIX}/", headers=bearer(tokens["access_token"]))
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_user_self_ok_200(aiohttp_client):
    created = await register_user(aiohttp_client, "get_self")
    tokens = await login(aiohttp_client, "get_self")

    resp = await aiohttp_client.get(f"{USERS_PREFIX}/{created['id']}", headers=bearer(tokens["access_token"]))
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert data["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_user_other_forbidden_403(aiohttp_client):
    u1 = await register_user(aiohttp_client, "get_a")
    u2 = await register_user(aiohttp_client, "get_b")
    tokens = await login(aiohttp_client, "get_a")

    resp = await aiohttp_client.get(f"{USERS_PREFIX}/{u2['id']}", headers=bearer(tokens["access_token"]))
    assert resp.status == 403, await resp.text()
    data = await resp.json()
    assert data["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_user_other_admin_ok_200(aiohttp_client):
    target = await register_user(aiohttp_client, "target_user")
    await register_user(aiohttp_client, "admin_user", role="admin")
    tokens = await login(aiohttp_client, "admin_user")

    resp = await aiohttp_client.get(f"{USERS_PREFIX}/{target['id']}", headers=bearer(tokens["access_token"]))
    assert resp.status == 200, await resp.text()


@pytest.mark.asyncio
async def test_update_user_self_ok_200(aiohttp_client):
    created = await register_user(aiohttp_client, "upd_self")
    tokens = await login(aiohttp_client, "upd_self")

    resp = await aiohttp_client.patch(
        f"{USERS_PREFIX}/{created['id']}",
        json={"first_name": "NewName"},
        headers=bearer(tokens["access_token"]),
    )
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert data["first_name"] == "NewName"


@pytest.mark.asyncio
async def test_change_password_self_ok_204_and_login_new_password(aiohttp_client):
    login_name = "pwd_user"
    old_password = "StrongPass123!"
    new_password = "NewStrongPass123!"

    created = await register_user(aiohttp_client, login_name, password=old_password)
    tokens = await login(aiohttp_client, login_name, password=old_password)

    resp = await aiohttp_client.post(
        f"{USERS_PREFIX}/{created['id']}/change-password",
        json={"old_password": old_password, "new_password": new_password},
        headers=bearer(tokens["access_token"]),
    )
    assert resp.status == 204, await resp.text()

    # старый пароль не работает
    bad = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={"login": login_name, "password": old_password})
    assert bad.status == 401, await bad.text()

    # новый пароль работает
    ok = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={"login": login_name, "password": new_password})
    assert ok.status == 200, await ok.text()
