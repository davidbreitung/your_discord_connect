"""Member identity, presence and voice channel sensors."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .bot_entity import BotEntity
from .const import MEMBER_SENSOR_KEYS
from .entity import DiscordMemberEntity, add_member_entities
from .groups import CENTRAL_KEYS, central_device_info
from .voice import PLAYBACK_STATES

KEYS = MEMBER_SENSOR_KEYS


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [DiscordCountSensor(entry.runtime_data, key) for key in CENTRAL_KEYS]
        + [BotPlaybackSensor(entry.runtime_data, "playback_status")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )
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
        elif key in ("last_present", "last_absent", "last_gateway_event"):
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> str | datetime | None:
        member = self.coordinator.data.get(self.member_id)
        return getattr(member, self.key) if member else None


class BotPlaybackSensor(BotEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(PLAYBACK_STATES)
    _attr_icon = "mdi:play-circle-outline"

    @property
    def native_value(self):
        return self.coordinator.voice.playback_state

    @property
    def extra_state_attributes(self):
        voice = self.coordinator.voice
        return {
            "queued_announcements": voice.queued_announcements,
            "last_audio_frames": voice.last_audio_frames,
            "last_audio_peak": voice.last_audio_peak,
            **voice.last_transport,
        }


class DiscordCountSensor(CoordinatorEntity, SensorEntity):
    """Exact counts from the same successful member snapshot as the devices."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:account-group"

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self.key = key
        self._attr_unique_id = f"{coordinator.guild_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = central_device_info(coordinator.guild_id)

    @property
    def native_value(self) -> int | None:
        members = self.coordinator.data.values()
        if self.key == "member_count":
            return len(self.coordinator.data)
        count = 0
        for member in members:
            if self.key == "voice_count":
                if member.in_voice_channel is None:
                    return None
                count += member.in_voice_channel
            elif member.presence in ("online", "idle", "dnd") or member.in_voice_channel:
                count += 1
            elif member.presence != "offline" or member.in_voice_channel is None:
                return None
        return count
