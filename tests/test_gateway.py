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
    guild.id = 100
    guild.afk_channel = None
    guild.query_members = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=1,
                status="online",
                guild=guild,
                voice=SimpleNamespace(
                    self_deaf=False,
                    deaf=False,
                    self_mute=False,
                    mute=False,
                    channel=SimpleNamespace(name="Lounge", id=10),
                ),
            ),
            SimpleNamespace(id=2, status="offline", voice=None, guild=guild),
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
        assert snapshot["1"].voice_channel_id == "10"
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
        SimpleNamespace(
            id=1,
            status="dnd",
            guild=client.get_guild.return_value,
            voice=SimpleNamespace(
                self_deaf=False, deaf=False, self_mute=False, mute=False, channel=None
            ),
        )
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


async def test_gateway_events_are_targeted_and_include_voice_flags(hass, client):
    updates = MagicMock()
    gateway = DiscordGateway(hass, "test-token", "100")
    gateway.on_member_update = updates
    guild = client.get_guild.return_value
    channel = SimpleNamespace(id=10, name="AFK")
    guild.afk_channel = channel
    voice = SimpleNamespace(channel=channel, self_mute=False, mute=True, self_deaf=True, deaf=False)
    member = SimpleNamespace(id=1, guild=guild, status="offline", voice=voice)
    try:
        await gateway.snapshot(["1"])
        updates.assert_not_called()  # Queries are not gateway events for the user timestamp.
        await client.on_voice_state_update(member, None, voice)
        uid, event = updates.call_args.args
        assert uid == "1"
        assert event.in_afk_channel is True
        assert event.microphone_muted is True
        assert event.speaker_muted is True
        assert event.in_voice_channel is True
        assert event.last_gateway_event is not None
        await client.on_presence_update(member, member)
        assert updates.call_count == 2
        await client.on_disconnect()
        await client.on_voice_state_update(member, voice, None)
        assert updates.call_count == 2
        await client.on_resumed()
        member.guild = SimpleNamespace(id=200, unavailable=False)
        await client.on_presence_update(member, member)
        assert updates.call_count == 2
    finally:
        await gateway.async_close()


async def test_guild_outage_notifies_connection_without_user_event(hass, client):
    gateway = DiscordGateway(hass, "test-token", "100")
    gateway.on_member_update = MagicMock()
    callback = gateway.on_connection_change = MagicMock()
    try:
        await gateway.snapshot(["1"])
        callback.reset_mock()
        await client.on_guild_unavailable(SimpleNamespace(id=200))
        callback.assert_not_called()
        await client.on_guild_unavailable(SimpleNamespace(id=100))
        callback.assert_called_once_with(False)
        await client.on_guild_available(SimpleNamespace(id=100))
        assert callback.call_args.args == (True,)
        gateway.on_member_update.assert_not_called()
    finally:
        await gateway.async_close()


async def test_channel_refresh_and_gateway_channel_events(hass, client):
    guild = client.get_guild.return_value
    guild.voice_channels = []
    guild.stage_channels = []
    channel = SimpleNamespace(id=10, name="Old", type=discord.ChannelType.voice, guild=guild)
    text = SimpleNamespace(id=11, name="Text", type=discord.ChannelType.text, guild=guild)
    stage = SimpleNamespace(id=12, name="Stage", type=discord.ChannelType.stage_voice, guild=guild)
    guild.fetch_channels = AsyncMock(return_value=[channel, text, stage])
    gateway = DiscordGateway(hass, "test-token", "100")
    gateway.on_bot_update = MagicMock()
    try:
        await gateway.snapshot(["1"])
        await gateway.refresh_channels()
        assert [c.id for c in gateway.channels] == [10, 12]
        renamed = SimpleNamespace(id=10, name="New", type=discord.ChannelType.voice, guild=guild)
        await client.on_guild_channel_update(channel, renamed)
        assert gateway.channels[-1].name == "New"
        await client.on_guild_channel_delete(stage)
        assert [c.id for c in gateway.channels] == [10]

        # An event received during an older HTTP request must not be overwritten.
        async def fetch():
            await client.on_guild_channel_update(channel, renamed)
            return [channel]

        guild.fetch_channels.side_effect = fetch
        await gateway.refresh_channels()
        assert gateway.channels[0].name == "New"
        guild.fetch_channels.side_effect = None
        guild.fetch_channels.return_value = [stage]
        await gateway.refresh_channels()
        assert [c.id for c in gateway.channels] == [12]
        assert guild.fetch_channels.await_count == 3
    finally:
        await gateway.async_close()
