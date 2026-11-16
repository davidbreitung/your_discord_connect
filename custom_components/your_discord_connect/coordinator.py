"""Fetch complete member snapshots at the configured interval."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DiscordAuthError, DiscordClient, DiscordError, Member
from .const import CONF_GUILD_ID, CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL, DOMAIN

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

    async def _async_update_data(self) -> dict[str, Member]:
        try:
            return await self.client.members(self.guild_id)
        except DiscordAuthError as err:
            raise ConfigEntryAuthFailed("Discord bot token is no longer valid") from err
        except DiscordError as err:
            raise UpdateFailed("Discord member synchronization failed") from err
