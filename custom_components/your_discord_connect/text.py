"""Editable announcement text; never spoken implicitly or restored on startup."""

from homeassistant.components.text import TextEntity, TextMode

from .bot_entity import BotEntity
from .entity import DiscordMemberEntity, add_member_entities
from .voice import MAX_TEXT_LENGTH


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [BotTTSText(entry.runtime_data, "tts_message")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )
    add_member_entities(
        entry,
        async_add_entities,
        lambda member_id: [PrivateMessageText(entry.runtime_data, member_id, "private_message")],
    )


class PrivateMessageText(DiscordMemberEntity, TextEntity):
    _attr_native_min = 0
    _attr_native_max = 255
    _attr_mode = TextMode.TEXT
    _attr_icon = "mdi:message-text-outline"

    @property
    def native_value(self):
        return self.coordinator.private_messages.get(self.member_id, "")

    async def async_set_value(self, value):
        if not isinstance(value, str) or len(value) > 255:
            from homeassistant.exceptions import ServiceValidationError

            raise ServiceValidationError("Maximum message length is 255 characters")
        self.coordinator.private_messages[self.member_id] = value
        self.coordinator.async_update_listeners()


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
