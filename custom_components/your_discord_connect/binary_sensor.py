"""A member's voice channel connection state."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import MEMBER_BINARY_KEYS
from .entity import DiscordMemberEntity, add_member_entities


async def async_setup_entry(hass, entry, async_add_entities):
    add_member_entities(
        entry,
        async_add_entities,
        lambda member_id: [
            DiscordVoiceSensor(entry.runtime_data, member_id, key) for key in MEMBER_BINARY_KEYS
        ],
    )


class DiscordVoiceSensor(DiscordMemberEntity, BinarySensorEntity):
    _attr_icon = "mdi:headset"

    @property
    def is_on(self) -> bool | None:
        member = self.coordinator.data.get(self.member_id)
        return getattr(member, self.key) if member else None
