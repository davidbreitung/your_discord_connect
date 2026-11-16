"""Fetch complete member snapshots at the configured interval."""

import logging
from dataclasses import asdict, replace
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .activity import ActivityTracker
from .api import DiscordAuthError, DiscordClient, DiscordError, Member
from .const import (
    CONF_GUILD_ID,
    CONF_SYNC_INTERVAL,
    DEFAULT_SYNC_INTERVAL,
    DOMAIN,
    MEMBER_BINARY_KEYS,
    MEMBER_SENSOR_KEYS,
)
from .dashboard import SIGNAL, FeedReader
from .gateway import DiscordGateway
from .groups import CENTRAL_KEYS
from .voice import BotVoice

_LOGGER = logging.getLogger(__name__)


class DiscordCoordinator(DataUpdateCoordinator[dict[str, Member]]):
    """Keep the last successful snapshot if any page fails."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL)
            ),
        )
        self.guild_id = entry.data[CONF_GUILD_ID]
        self.client = DiscordClient(async_get_clientsession(hass), entry.data[CONF_TOKEN])
        self.gateway = DiscordGateway(hass, entry.data[CONF_TOKEN], self.guild_id)
        self.voice = BotVoice(hass, self.gateway, self.guild_id)
        self.entry_id = entry.entry_id
        self.feed = FeedReader(self)
        self.activity = ActivityTracker(hass, self.guild_id)
        self.private_messages = {}
        self.sending_messages = set()
        self._syncing = False
        self._pending_updates = {}
        self.gateway.on_member_update = self._handle_gateway_update
        self.gateway.on_connection_change = self._handle_connection_change
        self.gateway.on_channels_update = self.async_update_listeners

    @callback
    def async_update_listeners(self):
        super().async_update_listeners()
        async_dispatcher_send(self.hass, SIGNAL)

    def _handle_gateway_update(self, member_id, state):
        if self.data is None or member_id not in self.data:
            return  # New members are discovered by the full membership sync.
        member = self.activity.observe(replace(self.data[member_id], **asdict(state)))
        self.data = {**self.data, member_id: member}
        if self._syncing:
            self._pending_updates[member_id] = state
        self.activity.schedule_save()
        # Unlike async_set_updated_data this does not restart the polling timer.
        self.async_update_listeners()

    def _handle_connection_change(self, connected):
        if self.data is None:
            return
        if not connected:
            self.async_set_update_error(UpdateFailed("Discord gateway disconnected"))
        elif not self._syncing:
            self.hass.async_create_task(self.async_request_refresh())

    async def async_close(self):
        self.private_messages.clear()
        self.feed._cache.clear()
        try:
            await self.voice.async_close()
        finally:
            try:
                await self.gateway.async_close()
            finally:
                await self.activity.close()

    @property
    def bot_id(self):
        return self.gateway.bot_id

    async def _async_update_data(self) -> dict[str, Member]:
        self._syncing = True
        self._pending_updates = {}
        try:
            await self.activity.load()
            members = await self.client.members(self.guild_id)
            states = await self.gateway.snapshot(list(members))
            await self.gateway.refresh_channels()
            states = {**states, **self._pending_updates}
            snapshot = {
                member_id: self.activity.observe(
                    replace(member, **asdict(state)) if (state := states.get(member_id)) else member
                )
                for member_id, member in members.items()
            }
            self.activity.records = {
                key: value for key, value in self.activity.records.items() if key in members
            }
            self.activity.schedule_save()
            self.private_messages = {
                key: value for key, value in self.private_messages.items() if key in members
            }
            self._reconcile_registry(snapshot)
            return snapshot
        except DiscordAuthError as err:
            raise ConfigEntryAuthFailed("Discord bot token is no longer valid") from err
        except DiscordError as err:
            raise UpdateFailed(str(err) or "Discord member synchronization failed") from err
        finally:
            self._syncing = False

    def _reconcile_registry(self, members: dict[str, Member]) -> None:
        """Clean up all member platforms only after both sources succeeded."""
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        prefix = f"{self.guild_id}_"
        valid_ids = {f"{prefix}{member_id}" for member_id in members if member_id != self.bot_id}
        keys = (*MEMBER_SENSOR_KEYS, *MEMBER_BINARY_KEYS)
        valid_entities = {f"{identifier}_{key}" for identifier in valid_ids for key in keys}
        valid_entities.update(f"{self.guild_id}_{key}" for key in CENTRAL_KEYS)
        valid_entities.add(f"{self.guild_id}_playback_status")
        valid_ids.add(f"{self.guild_id}_central")
        valid_ids.add(f"{self.guild_id}_bot")
        for entity in er.async_entries_for_config_entry(entities, self.entry_id):
            if (
                entity.platform == DOMAIN
                and entity.domain in ("sensor", "binary_sensor")
                and entity.unique_id not in valid_entities
            ):
                entities.async_remove(entity.entity_id)
        for device in dr.async_entries_for_config_entry(devices, self.entry_id):
            identifiers = {
                identifier for domain, identifier in device.identifiers if domain == DOMAIN
            }
            if identifiers and not identifiers.intersection(valid_ids):
                devices.async_remove_device(device.id)
        for member_id, member in members.items():
            if device := devices.async_get_device_by_identifier(
                (DOMAIN, f"{prefix}{member_id}"), self.entry_id
            ):
                if device.name != member.display_name:
                    devices.async_update_device(device.id, name=member.display_name)
        if bot := devices.async_get_device_by_identifier(
            (DOMAIN, f"{self.guild_id}_bot"), self.entry_id
        ):
            name = f"Bot: {self.gateway.bot_name}"
            if bot.name != name:
                devices.async_update_device(bot.id, name=name)
