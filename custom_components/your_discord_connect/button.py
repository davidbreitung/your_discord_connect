"""Manual synchronization for all members of a server."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .bot_entity import BotEntity
from .groups import central_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [DiscordSyncButton(entry.runtime_data), BotTTSButton(entry.runtime_data, "tts_execute")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )


class DiscordSyncButton(ButtonEntity):
    """Remain usable after a failed update so the user can retry."""

    _attr_translation_key = "sync"
    _attr_has_entity_name = True
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.guild_id}_sync"
        self._attr_device_info = central_device_info(coordinator.guild_id)

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError("Discord synchronization failed; check the integration status")


class BotTTSButton(BotEntity, ButtonEntity):
    _attr_icon = "mdi:account-voice"

    async def async_press(self):
        await self.coordinator.voice.speak()
