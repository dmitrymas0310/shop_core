import pytest

AUTH_PREFIX = "/api/v1/auth"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_auth_registrate_ok(aiohttp_client):
    payload = {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "login": "auth_reg_ok",
        "password": "StrongPass123!",
        "role": "user",
    }

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json=payload)
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert "id" in data
    assert data["login"] == "auth_reg_ok"


@pytest.mark.asyncio
async def test_auth_registrate_validation_422(aiohttp_client):
    payload = {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "login": "auth_reg_422",
        "role": "user",
    }

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json=payload)
    assert resp.status == 422, await resp.text()


@pytest.mark.asyncio
async def test_auth_token_ok(aiohttp_client):
    # register
    await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "auth_token_ok",
        "password": "StrongPass123!",
        "role": "user",
    })

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": "auth_token_ok",
        "password": "StrongPass123!",
    })
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data and len(data["access_token"]) > 10
    assert "refresh_token" in data and len(data["refresh_token"]) > 10


@pytest.mark.asyncio
async def test_auth_token_wrong_password_401(aiohttp_client):
    await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "auth_bad_pwd",
        "password": "StrongPass123!",
        "role": "user",
    })

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": "auth_bad_pwd",
        "password": "WRONG",
    })
    assert resp.status == 401, await resp.text()

    data = await resp.json()
    assert data["detail"] == "Incorrect login or password"


@pytest.mark.asyncio
async def test_auth_users_me_requires_auth(aiohttp_client):
    resp = await aiohttp_client.get(f"{AUTH_PREFIX}/users/me")
    assert resp.status in (401, 403), await resp.text()


@pytest.mark.asyncio
async def test_auth_users_me_ok(aiohttp_client):
    await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Me",
        "last_name": "User",
        "login": "auth_me_ok",
        "password": "StrongPass123!",
        "role": "user",
    })

    tok_resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": "auth_me_ok",
        "password": "StrongPass123!",
    })
    assert tok_resp.status == 200, await tok_resp.text()
    tokens = await tok_resp.json()

    resp = await aiohttp_client.get(
        f"{AUTH_PREFIX}/users/me",
        headers=bearer(tokens["access_token"])
    )
    assert resp.status == 200, await resp.text()
    data = await resp.json()
    assert data["login"] == "auth_me_ok"


@pytest.mark.asyncio
async def test_auth_refresh_ok(aiohttp_client):
    await aiohttp_client.post(f"{AUTH_PREFIX}/registrate", json={
        "first_name": "Ref",
        "last_name": "User",
        "login": "auth_refresh_ok",
        "password": "StrongPass123!",
        "role": "user",
    })

    tok_resp = await aiohttp_client.post(f"{AUTH_PREFIX}/token", json={
        "login": "auth_refresh_ok",
        "password": "StrongPass123!",
    })
    assert tok_resp.status == 200, await tok_resp.text()
    tokens = await tok_resp.json()

    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert resp.status == 200, await resp.text()

    data = await resp.json()
    assert "access_token" in data and len(data["access_token"]) > 10
    assert "refresh_token" in data and len(data["refresh_token"]) > 10


@pytest.mark.asyncio
async def test_auth_refresh_invalid_token_401_or_403(aiohttp_client):
    resp = await aiohttp_client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": "not_a_jwt"})
    assert resp.status in (401, 403), await resp.text()
