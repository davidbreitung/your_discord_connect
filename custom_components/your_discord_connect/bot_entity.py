"""Entities belonging to the central bot device."""

from homeassistant.helpers.entity import Entity

from .groups import bot_device_info


class BotEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, key):
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.guild_id}_{key}"
        self._attr_translation_key = key

    @property
    def device_info(self):
        return bot_device_info(self.coordinator)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.voice.add_listener(self.async_write_ha_state))
