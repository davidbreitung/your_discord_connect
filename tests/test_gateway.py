"""Gateway lifecycle and snapshots without Discord network access."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from custom_components.your_discord_connect.api import (
    DiscordAuthError,
    DiscordError,
    DiscordPermissionError,
)
from custom_components.your_discord_connect.gateway import DiscordGateway


@pytest.fixture
def client():
    client = MagicMock()
    client.event.side_effect = lambda callback: setattr(client, callback.__name__, callback)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.is_ready.return_value = True
    client.close = AsyncMock()
    running = asyncio.Event()

    async def start(*args, **kwargs):
        await client.on_ready()
        await running.wait()

    client.start = AsyncMock(side_effect=start)
    guild = client.get_guild.return_value
    guild.unavailable = False
    guild.query_members = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=1, status="online", voice=SimpleNamespace(channel=SimpleNamespace(name="Lounge"))
            ),
            SimpleNamespace(id=2, status="offline", voice=None),
        ]
    )
    with patch(
        "custom_components.your_discord_connect.gateway.discord.Client", return_value=client
    ):
        yield client


async def test_snapshot_batches_and_closes(hass, client):
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        snapshot = await gateway.snapshot([str(i) for i in range(1, 102)])
        assert snapshot["1"].presence == "online"
        assert snapshot["1"].in_voice_channel is True
        assert snapshot["1"].voice_channel == "Lounge"
        assert snapshot["2"].in_voice_channel is False
        assert snapshot["2"].voice_channel is None
        query = client.get_guild.return_value.query_members
        assert query.await_count == 2
        assert len(query.call_args_list[0].kwargs["user_ids"]) == 100
        assert query.call_args_list[1].kwargs == {
            "user_ids": [101],
            "presences": True,
            "cache": True,
        }
        await gateway.snapshot(["1"])
        assert client.start.await_count == 1
        task = gateway._task
    finally:
        await gateway.async_close()
    client.close.assert_awaited_once()
    assert task.done()


@pytest.mark.parametrize(
    "failure,expected",
    [
        (discord.LoginFailure("invalid"), DiscordAuthError),
        (discord.PrivilegedIntentsRequired(None), DiscordPermissionError),
        (OSError("connection lost"), DiscordError),
    ],
)
async def test_terminal_gateway_errors(hass, client, failure, expected):
    client.start.side_effect = failure
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        with pytest.raises(expected):
            await gateway.snapshot(["1"])
    finally:
        await gateway.async_close()


async def test_disconnect_during_query_rejects_snapshot(hass, client):
    async def query(**kwargs):
        await client.on_disconnect()
        return []

    client.get_guild.return_value.query_members.side_effect = query
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        with pytest.raises(DiscordError, match="disconnected during"):
            await gateway.snapshot(["1"])
    finally:
        await gateway.async_close()


async def test_unavailable_guild_rejects_snapshot(hass, client):
    client.get_guild.return_value.unavailable = True
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        with pytest.raises(DiscordError, match="server is unavailable"):
            await gateway.snapshot(["1"])
    finally:
        await gateway.async_close()


async def test_close_before_start(hass):
    gateway = DiscordGateway(hass, "test-token", "100")
    await gateway.async_close()
    assert gateway._task is None


async def test_voice_without_resolved_channel_name(hass, client):
    client.get_guild.return_value.query_members.return_value = [
        SimpleNamespace(id=1, status="dnd", voice=SimpleNamespace(channel=None))
    ]
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        snapshot = await gateway.snapshot(["1"])
        assert snapshot["1"].in_voice_channel is True
        assert snapshot["1"].voice_channel is None
    finally:
        await gateway.async_close()


async def test_resumed_connection_is_reused(hass, client):
    gateway = DiscordGateway(hass, "test-token", "100")
    try:
        await gateway.snapshot(["1"])
        await client.on_disconnect()
        assert not gateway._ready.is_set()
        await client.on_resumed()
        assert (await gateway.snapshot(["1"]))["1"].presence == "online"
        client.start.assert_awaited_once()
    finally:
        await gateway.async_close()
