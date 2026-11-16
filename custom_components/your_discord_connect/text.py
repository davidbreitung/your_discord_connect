"""Editable announcement text; never spoken implicitly or restored on startup."""

from homeassistant.components.text import TextEntity, TextMode

from .bot_entity import BotEntity
from .voice import MAX_TEXT_LENGTH


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [BotTTSText(entry.runtime_data, "tts_message")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )


class BotTTSText(BotEntity, TextEntity):
    _attr_native_min = 0
    _attr_native_max = MAX_TEXT_LENGTH
    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:text-to-speech"

    @property
    def native_value(self):
        return self.coordinator.voice.text

    async def async_set_value(self, value):
        self.coordinator.voice.set_text(value)
