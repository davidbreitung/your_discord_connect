"""Persistent volume for the bot's announcement output."""

from homeassistant.components.number import NumberEntity, NumberMode

from .bot_entity import BotEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [BotVolumeNumber(entry.runtime_data, "volume")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )


class BotVolumeNumber(BotEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:volume-high"

    @property
    def native_value(self):
        return self.coordinator.voice.volume

    async def async_set_native_value(self, value):
        await self.coordinator.voice.async_set_volume(value)
