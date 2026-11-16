"""Member identity, presence and voice channel sensors."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .entity import DiscordMemberEntity, add_member_entities

KEYS = ("display_name", "username", "presence", "voice_channel")


async def async_setup_entry(hass, entry, async_add_entities):
    add_member_entities(
        entry,
        async_add_entities,
        lambda member_id: [DiscordMemberSensor(entry.runtime_data, member_id, key) for key in KEYS],
    )


class DiscordMemberSensor(DiscordMemberEntity, SensorEntity):
    """Publish the coordinator snapshot, never a mutable live gateway member."""

    def __init__(self, coordinator, member_id, key):
        super().__init__(coordinator, member_id, key)
        self._attr_icon = "mdi:account" if key != "voice_channel" else "mdi:volume-high"
        if key == "presence":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["online", "idle", "dnd", "offline"]

    @property
    def native_value(self) -> str | None:
        member = self.coordinator.data.get(self.member_id)
        return getattr(member, self.key) if member else None
