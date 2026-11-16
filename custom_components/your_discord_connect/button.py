"""Manual synchronization for all members of a server."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .bot_entity import BotEntity
from .const import DOMAIN
from .entity import DiscordMemberEntity, add_member_entities
from .groups import central_device_info
from .services import async_send_direct_message


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [DiscordSyncButton(entry.runtime_data), BotTTSButton(entry.runtime_data, "tts_execute")],
        config_subentry_id=entry.runtime_data.groups["central"],
    )
    add_member_entities(
        entry,
        async_add_entities,
        lambda member_id: [
            PrivateMessageButton(entry.runtime_data, member_id, "private_message_send")
        ],
    )


class PrivateMessageButton(DiscordMemberEntity, ButtonEntity):
    _attr_icon = "mdi:send"

    async def async_press(self):
        coordinator = self.coordinator
        if self.member_id in coordinator.sending_messages:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="dm_sending")
        device = dr.async_get(self.hass).async_get_device_by_identifier(
            (DOMAIN, self._identifier), coordinator.entry_id
        )
        content = coordinator.private_messages.get(self.member_id, "")
        coordinator.sending_messages.add(self.member_id)
        try:
            await async_send_direct_message(self.hass, device.id if device else None, content)
            if coordinator.private_messages.get(self.member_id) == content:
                coordinator.private_messages.pop(self.member_id, None)
                coordinator.async_update_listeners()
        finally:
            coordinator.sending_messages.discard(self.member_id)


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
