"""Your Discord Connect integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .activity import ActivityTracker
from .const import CONF_GUILD_ID
from .coordinator import DiscordCoordinator
from .groups import setup_groups
from .services import async_register_services

type DiscordConfigEntry = ConfigEntry[DiscordCoordinator]
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DiscordConfigEntry) -> bool:
    coordinator = DiscordCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        setup_groups(hass, entry, coordinator)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await coordinator.async_close()
        raise
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    async def stop_gateway(event):
        await coordinator.async_close()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_gateway))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: DiscordConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DiscordConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_close()
        return True
    return False


async def async_remove_entry(hass: HomeAssistant, entry: DiscordConfigEntry) -> None:
    await ActivityTracker(hass, entry.data[CONF_GUILD_ID]).store.async_remove()
