"""Fetch complete member snapshots at the configured interval."""

import logging
from dataclasses import replace
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DiscordAuthError, DiscordClient, DiscordError, Member
from .const import CONF_GUILD_ID, CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL, DOMAIN
from .gateway import DiscordGateway

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
        self.entry_id = entry.entry_id

    async def _async_update_data(self) -> dict[str, Member]:
        try:
            members = await self.client.members(self.guild_id)
            states = await self.gateway.snapshot(list(members))
            snapshot = {
                member_id: replace(
                    member,
                    presence=state.presence,
                    in_voice_channel=state.in_voice_channel,
                    voice_channel=state.voice_channel,
                )
                if (state := states.get(member_id))
                else member
                for member_id, member in members.items()
            }
            self._reconcile_registry(snapshot)
            return snapshot
        except DiscordAuthError as err:
            raise ConfigEntryAuthFailed("Discord bot token is no longer valid") from err
        except DiscordError as err:
            raise UpdateFailed(str(err) or "Discord member synchronization failed") from err

    def _reconcile_registry(self, members: dict[str, Member]) -> None:
        """Clean up all member platforms only after both sources succeeded."""
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        prefix = f"{self.guild_id}_"
        valid_ids = {f"{prefix}{member_id}" for member_id in members}
        keys = ("display_name", "username", "presence", "voice_channel", "in_voice_channel")
        valid_entities = {f"{identifier}_{key}" for identifier in valid_ids for key in keys}
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
