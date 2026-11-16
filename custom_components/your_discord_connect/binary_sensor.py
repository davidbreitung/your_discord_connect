"""A member's voice channel connection state."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import DiscordMemberEntity, add_member_entities


async def async_setup_entry(hass, entry, async_add_entities):
    add_member_entities(
        entry,
        async_add_entities,
        lambda member_id: [DiscordVoiceSensor(entry.runtime_data, member_id, "in_voice_channel")],
    )


class DiscordVoiceSensor(DiscordMemberEntity, BinarySensorEntity):
    _attr_icon = "mdi:headset"

    @property
    def is_on(self) -> bool | None:
        member = self.coordinator.data.get(self.member_id)
        return member.in_voice_channel if member else None
