"""Dashboard ordering, channel isolation, websocket permissions and shared caching."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.your_discord_connect.api import DiscordPermissionError, Member, avatar_url
from custom_components.your_discord_connect.const import DOMAIN
from custom_components.your_discord_connect.dashboard import FeedReader, overview


def channel(channel_id, name, kind, position=0, parent=None, visible=True, history=True):
    return SimpleNamespace(
        id=channel_id,
        name=name,
        type=kind,
        position=position,
        category_id=parent.id if parent else None,
        category=parent,
        permissions_for=lambda _: SimpleNamespace(
            view_channel=visible, read_message_history=history
        ),
    )


@pytest.fixture
def dashboard_data():
    # Hidden category with a visible child must still be shown, just as in Discord.
    category = channel(10, "Gaming", discord.ChannelType.category, 5, visible=False)
    early = channel(9, "General", discord.ChannelType.category, 0)
    channels = [
        category,
        channel(21, "Same name", discord.ChannelType.voice, 2, category),
        channel(20, "Same name", discord.ChannelType.voice, 1, category),
        channel(22, "Hidden", discord.ChannelType.voice, 0, category, visible=False),
        channel(30, "chat", discord.ChannelType.text, parent=category),
        early,
        channel(19, "Stage", discord.ChannelType.stage_voice, 0, early),
        channel(18, "Uncategorized", discord.ChannelType.voice),
    ]
    return SimpleNamespace(
        gateway=SimpleNamespace(all_channels=channels, guild=SimpleNamespace(me=object())),
        data={
            "1": Member("1", "Alice", voice_channel_id="20", microphone_muted=True),
            "2": Member("2", "Bob", voice_channel_id="21"),
        },
        bot_id=None,
        last_update_success=True,
        client=SimpleNamespace(_get=AsyncMock(return_value=[])),
    )


def test_hierarchy_duplicate_names_and_member_permission(dashboard_data):
    result = overview(dashboard_data)
    assert [g["name"] for g in result["groups"]] == [None, "General", "Gaming"]
    channels = result["groups"][2]["channels"]
    assert [c["id"] for c in channels] == ["20", "21"]
    assert channels[0]["members"][0]["name"] == "Alice"
    assert channels[0]["members"][0]["microphone_muted"]
    assert channels[1]["members"][0]["name"] == "Bob"
    assert (
        overview(dashboard_data, lambda uid: uid != "1")["groups"][2]["channels"][0]["members"]
        == []
    )


async def test_feed_cache_and_permission_revocation(dashboard_data):
    reader = FeedReader(dashboard_data)
    dashboard_data.client._get.return_value = [
        {
            "id": "1",
            "author": {"id": "2", "username": "bob"},
            "content": "<script>unsafe()</script>",
            "timestamp": "2026-11-16T12:00:00Z",
        }
    ]
    result = await reader.read("30")
    assert result["messages"][0]["content"] == "<script>unsafe()</script>"
    assert await reader.read("30") == result
    dashboard_data.client._get.assert_awaited_once_with("/channels/30/messages", {"limit": 50})
    for other in ["999", "20", "22"]:
        with pytest.raises(DiscordPermissionError):
            await reader.read(other)
    chat = next(c for c in dashboard_data.gateway.all_channels if c.id == 30)
    chat.permissions_for = lambda _: SimpleNamespace(view_channel=True, read_message_history=False)
    with pytest.raises(DiscordPermissionError):
        await reader.read("30")
    assert not reader._cache


async def test_feed_edits_deletes_and_expiry(dashboard_data):
    reader = FeedReader(dashboard_data)
    with patch("custom_components.your_discord_connect.dashboard.monotonic", return_value=0):
        await reader.read("30")
    dashboard_data.client._get.return_value = [
        {
            "id": "2",
            "author": {"id": "1", "username": "alice"},
            "content": "Edited",
            "timestamp": "2026-11-16T12:00:00Z",
            "edited_timestamp": "2026-11-16T12:01:00Z",
            "attachments": [
                {
                    "filename": "image.png",
                    "url": "https://cdn.discordapp.com/attachments/test.png",
                    "content_type": "image/png",
                }
            ],
        }
    ]
    with patch("custom_components.your_discord_connect.dashboard.monotonic", return_value=16):
        result = await reader.read("30")
    assert result["messages"][0]["edited"]
    assert result["messages"][0]["attachments"][0]["image"]
    dashboard_data.client._get.return_value = []
    with patch("custom_components.your_discord_connect.dashboard.monotonic", return_value=32):
        assert (await reader.read("30"))["messages"] == []


def test_avatar_precedence():
    user = {"id": "12345", "avatar": "global"}
    assert "/guilds/100/users/12345/avatars/local" in avatar_url(user, {"avatar": "local"}, "100")
    assert "/avatars/12345/global" in avatar_url(user)
    assert avatar_url({"id": "12345"}).endswith("/0.png")


@pytest.mark.usefixtures("discord", "gateway")
async def test_websocket_subscription_and_feed_access(hass, entry, hass_ws_client, dashboard_data):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/servers"})
    response = await client.receive_json()
    assert response["result"] == [{"id": entry.entry_id, "name": "Test server"}]
    with (
        patch.object(entry.runtime_data.gateway, "_channels", dashboard_data.gateway.all_channels),
        patch(
            "custom_components.your_discord_connect.gateway.DiscordGateway.guild",
            new_callable=lambda: property(lambda _: dashboard_data.gateway.guild),
        ),
    ):
        await client.send_json({"id": 2, "type": f"{DOMAIN}/overview", "entry_id": entry.entry_id})
        assert (await client.receive_json())["success"]
        assert (await client.receive_json())["event"]["available"]
        entry.runtime_data.async_update_listeners()
        assert (await client.receive_json())["type"] == "event"
        await client.send_json({"id": 3, "type": "unsubscribe_events", "subscription": 2})
        assert (await client.receive_json())["success"]
        with patch.object(entry.runtime_data.client, "_get", new=AsyncMock(return_value=[])) as get:
            await client.send_json(
                {"id": 4, "type": f"{DOMAIN}/feed", "entry_id": entry.entry_id, "channel_id": "999"}
            )
            assert not (await client.receive_json())["success"]
            get.assert_not_awaited()
            await client.send_json(
                {"id": 5, "type": f"{DOMAIN}/feed", "entry_id": entry.entry_id, "channel_id": "30"}
            )
            assert (await client.receive_json())["result"]["messages"] == []
    await client.close()


@pytest.mark.usefixtures("discord", "gateway")
async def test_websocket_denies_central_entity_permission(
    hass, entry, hass_ws_client, hass_admin_user
):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    central = er.async_get(hass).async_get_entity_id("button", DOMAIN, "100_sync")
    assert central
    with patch.object(type(hass_admin_user.permissions), "check_entity", return_value=False):
        await client.send_json({"id": 1, "type": f"{DOMAIN}/servers"})
        assert (await client.receive_json())["result"] == []
        await client.send_json({"id": 2, "type": f"{DOMAIN}/overview", "entry_id": entry.entry_id})
        assert not (await client.receive_json())["success"]
    await client.close()


@pytest.mark.usefixtures("discord", "gateway")
async def test_frontend_module_is_served_by_home_assistant(hass, entry, hass_client):
    from custom_components.your_discord_connect.dashboard import STATIC_URL

    assert await hass.config_entries.async_setup(entry.entry_id)
    client = await hass_client()
    response = await client.get(STATIC_URL)
    assert response.status == 200
    source = await response.text()
    assert "discord-channel-overview" in source
    assert "discord-text-channel-feed" in source
    assert "test-token" not in source
