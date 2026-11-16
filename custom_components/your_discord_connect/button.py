"""Manual synchronization for all members of a server."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DiscordSyncButton(entry.runtime_data, entry.title)])


class DiscordSyncButton(ButtonEntity):
    """Remain usable after a failed update so the user can retry."""

    _attr_translation_key = "sync"
    _attr_has_entity_name = True
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator, title):
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.guild_id}_sync"
        self._attr_translation_placeholders = {"server": title}

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError("Discord synchronization failed; check the integration status")
