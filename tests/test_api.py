"""Test actual HTTP requests, error mapping and full pagination."""

from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.your_discord_connect.api import (
    DiscordAuthError,
    DiscordClient,
    DiscordError,
    DiscordNotFoundError,
    DiscordPermissionError,
    DiscordRateLimitError,
)
from custom_components.your_discord_connect.const import API_BASE


def member(number, **kwargs):
    return {"user": {"id": str(number), "username": f"user{number}", **kwargs}}


async def test_names_and_auth(hass, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/guilds/100/members",
        json=[
            {**member(1, global_name="Global"), "nick": "Nickname"},
            member(2, global_name="Global"),
            member(3),
        ],
    )
    client = DiscordClient(async_get_clientsession(hass), "test-token")
    result = await client.members("100")
    assert [m.display_name for m in result.values()] == ["Nickname", "Global", "user3"]
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bot test-token"


async def test_member_pagination(hass, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/guilds/100/members?limit=1000&after=0",
        json=[member(i) for i in range(1, 1001)],
    )
    aioclient_mock.get(f"{API_BASE}/guilds/100/members?limit=1000&after=1000", json=[member(1001)])
    result = await DiscordClient(async_get_clientsession(hass), "test-token").members("100")
    assert len(result) == 1001
    assert aioclient_mock.call_count == 2


async def test_partial_failure_raises(hass, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/guilds/100/members?limit=1000&after=0",
        json=[member(i) for i in range(1, 1001)],
    )
    aioclient_mock.get(f"{API_BASE}/guilds/100/members?limit=1000&after=1000", status=503)
    with pytest.raises(DiscordError):
        await DiscordClient(async_get_clientsession(hass), "test-token").members("100")


@pytest.mark.parametrize(
    "status,error",
    [
        (401, DiscordAuthError),
        (403, DiscordPermissionError),
        (404, DiscordNotFoundError),
        (429, DiscordRateLimitError),
        (500, DiscordError),
    ],
)
async def test_http_errors(hass, aioclient_mock, status, error):
    aioclient_mock.get(f"{API_BASE}/guilds/100/members", status=status)
    with pytest.raises(error):
        await DiscordClient(async_get_clientsession(hass), "test-token").members("100")


async def test_guild_pagination(hass, aioclient_mock):
    aioclient_mock.get(
        f"{API_BASE}/users/@me/guilds?limit=200&after=0",
        json=[{"id": str(i), "name": f"Server {i}"} for i in range(1, 201)],
    )
    aioclient_mock.get(f"{API_BASE}/users/@me/guilds?limit=200&after=200", json=[])
    result = await DiscordClient(async_get_clientsession(hass), "test-token").guilds()
    assert len(result) == 200
    assert aioclient_mock.call_count == 2


@pytest.mark.parametrize("payload", [{}, None, {"message": "error"}, [None], [{"user": {}}]])
async def test_malformed_members_cannot_become_empty_snapshot(hass, aioclient_mock, payload):
    aioclient_mock.get(f"{API_BASE}/guilds/100/members", json=payload)
    with pytest.raises(DiscordError):
        await DiscordClient(async_get_clientsession(hass), "test-token").members("100")


async def test_rate_limit_cooldown(hass, aioclient_mock):
    aioclient_mock.get(f"{API_BASE}/guilds/100/members", status=429, headers={"Retry-After": "120"})
    client = DiscordClient(async_get_clientsession(hass), "test-token")
    with patch("custom_components.your_discord_connect.api.monotonic", return_value=100):
        with pytest.raises(DiscordRateLimitError):
            await client.members("100")
    with patch("custom_components.your_discord_connect.api.monotonic", return_value=160):
        with pytest.raises(DiscordRateLimitError):
            await client.members("100")
    assert aioclient_mock.call_count == 1
    with patch("custom_components.your_discord_connect.api.monotonic", return_value=221):
        with pytest.raises(DiscordRateLimitError):
            await client.members("100")
    assert aioclient_mock.call_count == 2
