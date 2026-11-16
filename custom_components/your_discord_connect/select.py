"""Select the bot's actual voice channel."""

from homeassistant.components.select import SelectEntity

from .bot_entity import BotEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [BotChannelSelect(entry.runtime_data, "bot_channel")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )


class BotChannelSelect(BotEntity, SelectEntity):
    _attr_icon = "mdi:headset"

    @property
    def options(self):
        return self.coordinator.voice.options

    @property
    def current_option(self):
        return self.coordinator.voice.current_option

    async def async_select_option(self, option):
        await self.coordinator.voice.select(option)
