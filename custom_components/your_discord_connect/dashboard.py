"""Authenticated dashboard data. Discord credentials never leave the backend."""

import asyncio
from collections import OrderedDict
from datetime import timedelta
from pathlib import Path
from time import monotonic

import discord
import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_interval

from .api import DiscordError, DiscordPermissionError, avatar_url
from .const import DOMAIN

SIGNAL = f"{DOMAIN}_dashboard"
STATIC_URL = "/your_discord_connect/discord-cards.js"


def accessible(hass, connection, entry):
    """Dashboard data has the same read boundary as the central sync entity."""
    entity_id = er.async_get(hass).async_get_entity_id("button", DOMAIN, f"{entry.unique_id}_sync")
    return bool(entity_id and connection.user.permissions.check_entity(entity_id, POLICY_READ))


def get_entry(hass, connection, entry_id):
    entry = hass.config_entries.async_get_entry(entry_id)
    if not entry or entry.domain != DOMAIN or not accessible(hass, connection, entry):
        raise ValueError("Discord server is unavailable or access is denied")
    if entry.state is not ConfigEntryState.LOADED:
        raise ValueError("Discord integration is not loaded")
    return entry


def visible_channels(coordinator):
    guild = coordinator.gateway.guild
    if not guild or not guild.me:
        return []
    return [
        channel
        for channel in coordinator.gateway.all_channels
        if channel.permissions_for(guild.me).view_channel
    ]


def overview(coordinator, member_allowed=lambda member_id: True):
    """Reproduce Discord's category/channel ordering, using IDs for voice membership."""
    channels = visible_channels(coordinator)
    categories = sorted(
        (c for c in coordinator.gateway.all_channels if c.type is discord.ChannelType.category),
        key=lambda c: (c.position, c.id),
    )
    voices = [
        c
        for c in channels
        if c.type in (discord.ChannelType.voice, discord.ChannelType.stage_voice)
    ]
    groups = []
    for category in [None, *categories]:
        category_id = category.id if category else None
        rows = []
        for channel in sorted(voices, key=lambda c: (c.position, c.id)):
            if channel.category_id != category_id:
                continue
            members = [
                {
                    "id": m.id,
                    "name": m.display_name,
                    "username": m.username,
                    "avatar": m.avatar_url,
                    "presence": m.presence,
                    "microphone_muted": m.microphone_muted,
                    "speaker_muted": m.speaker_muted,
                    "afk": m.in_afk_channel,
                    "bot": m.id == coordinator.bot_id,
                }
                for m in (coordinator.data or {}).values()
                if m.voice_channel_id == str(channel.id) and member_allowed(m.id)
            ]
            rows.append(
                {
                    "id": str(channel.id),
                    "name": channel.name,
                    "stage": channel.type is discord.ChannelType.stage_voice,
                    "members": sorted(members, key=lambda m: (m["name"].casefold(), m["id"])),
                }
            )
        if rows:
            groups.append(
                {
                    "id": str(category_id) if category else None,
                    "name": category.name if category else None,
                    "channels": rows,
                }
            )
    return {
        "available": coordinator.last_update_success,
        "groups": groups,
        "text_channels": [
            {"id": str(c.id), "name": c.name, "category": c.category.name if c.category else None}
            for c in channels
            if c.type in (discord.ChannelType.text, discord.ChannelType.news)
        ],
    }


class FeedReader:
    """Bounded, shared 15-second cache. No message contents in HA entity history."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._cache = OrderedDict()
        self._lock = asyncio.Lock()

    async def read(self, channel_id):
        async with self._lock:
            channel = next(
                (c for c in visible_channels(self.coordinator) if str(c.id) == channel_id), None
            )
            if (
                channel is None
                or channel.type not in (discord.ChannelType.text, discord.ChannelType.news)
                or not channel.permissions_for(
                    self.coordinator.gateway.guild.me
                ).read_message_history
            ):
                self._cache.pop(channel_id, None)
                raise DiscordPermissionError
            cached = self._cache.get(channel_id)
            if cached and monotonic() - cached[0] < 15:
                self._cache.move_to_end(channel_id)
                return cached[1]
            raw = await self.coordinator.client._get(
                f"/channels/{channel_id}/messages", {"limit": 50}
            )
            if not isinstance(raw, list):
                raise DiscordError("Invalid channel history")
            messages = []
            try:
                for item in reversed(raw):
                    author = item["author"]
                    member = (self.coordinator.data or {}).get(str(author["id"]))
                    messages.append(
                        {
                            "id": str(item["id"]),
                            "author": member.display_name
                            if member
                            else author.get("global_name") or author["username"],
                            "avatar": member.avatar_url
                            if member and member.avatar_url
                            else avatar_url(author),
                            "bot": bool(author.get("bot")),
                            "content": item.get("content", ""),
                            "timestamp": item["timestamp"],
                            "edited": item.get("edited_timestamp"),
                            "reply_to": (item.get("referenced_message") or {})
                            .get("author", {})
                            .get("username"),
                            "attachments": [
                                {
                                    "name": a["filename"],
                                    "url": a["url"],
                                    "image": str(a.get("content_type", "")).startswith("image/"),
                                }
                                for a in item.get("attachments", [])
                            ],
                            "embeds": [
                                {
                                    "title": e.get("title", ""),
                                    "description": e.get("description", ""),
                                    "url": e.get("url"),
                                }
                                for e in item.get("embeds", [])
                            ],
                        }
                    )
            except (KeyError, TypeError, ValueError) as err:
                raise DiscordError("Invalid channel history") from err
            result = {"channel": channel.name, "messages": messages}
            self._cache[channel_id] = (monotonic(), result)
            self._cache.move_to_end(channel_id)
            while len(self._cache) > 8:
                self._cache.popitem(last=False)
            return result


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/servers"})
@callback
def ws_servers(hass, connection, msg):
    connection.send_result(
        msg["id"],
        [
            {"id": entry.entry_id, "name": entry.title}
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED and accessible(hass, connection, entry)
        ],
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/overview",
        vol.Required("entry_id"): str,
    }
)
@callback
def ws_overview(hass, connection, msg):
    try:
        get_entry(hass, connection, msg["entry_id"])
    except ValueError as err:
        connection.send_error(msg["id"], "unavailable", str(err))
        return

    @callback
    def publish(*_):
        try:
            entry = get_entry(hass, connection, msg["entry_id"])
        except ValueError:
            connection.send_event(
                msg["id"], {"available": False, "groups": [], "text_channels": []}
            )
            return
        coordinator = entry.runtime_data

        def member_allowed(member_id):
            if member_id == coordinator.bot_id:
                return True
            entity_id = er.async_get(hass).async_get_entity_id(
                "sensor", DOMAIN, f"{coordinator.guild_id}_{member_id}_display_name"
            )
            return entity_id and connection.user.permissions.check_entity(entity_id, POLICY_READ)

        connection.send_event(
            msg["id"], {"server": entry.title, **overview(coordinator, member_allowed)}
        )

    unsubscribe = async_dispatcher_connect(hass, SIGNAL, publish)
    # Also recover when a config entry is unloaded/reloaded without a websocket reconnect.
    cancel_timer = async_track_time_interval(hass, publish, timedelta(seconds=15))

    @callback
    def cancel():
        unsubscribe()
        cancel_timer()

    connection.subscriptions[msg["id"]] = cancel
    connection.send_result(msg["id"])
    publish()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/feed",
        vol.Required("entry_id"): str,
        vol.Required("channel_id"): vol.All(str, vol.Match(r"^[0-9]{1,20}$")),
    }
)
@websocket_api.async_response
async def ws_feed(hass, connection, msg):
    try:
        entry = get_entry(hass, connection, msg["entry_id"])
        if not entry.runtime_data.last_update_success:
            raise ValueError("Discord is disconnected")
        coordinator = entry.runtime_data
        result = await coordinator.feed.read(msg["channel_id"])
        # Recheck after I/O, including permissions and integration unload/reload.
        if get_entry(hass, connection, msg["entry_id"]).runtime_data is not coordinator:
            raise ValueError("Discord integration changed")
    except ValueError as err:
        connection.send_error(msg["id"], "unavailable", str(err))
    except DiscordError:
        connection.send_error(
            msg["id"],
            "discord_error",
            "Cannot read channel. Check bot permissions, Message Content Intent "
            "and Discord connection.",
        )
    else:
        connection.send_result(msg["id"], result)


async def async_setup_dashboard(hass):
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                STATIC_URL, str(Path(__file__).parent / "frontend/discord-cards.js"), False
            )
        ]
    )
    for handler in (ws_servers, ws_overview, ws_feed):
        websocket_api.async_register_command(hass, handler)
