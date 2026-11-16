"""Shared member identity and dynamic entity discovery."""

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DiscordCoordinator


@callback
def add_member_entities(entry, async_add_entities, factory):
    """Register new members separately for each platform."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def reconcile():
        if not coordinator.last_update_success:
            return
        current = set(coordinator.data)
        current.discard(coordinator.bot_id)
        new = current - known
        known.intersection_update(current)
        known.update(new)
        async_add_entities(
            (entity for member_id in sorted(new) for entity in factory(member_id)),
            config_subentry_id=coordinator.groups["users"],
        )

    entry.async_on_unload(coordinator.async_add_listener(reconcile))
    reconcile()


class DiscordMemberEntity(CoordinatorEntity[DiscordCoordinator]):
    """All entities for a member attach to the existing stable device identifier."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DiscordCoordinator, member_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.member_id = member_id
        self.key = key
        self._identifier = f"{coordinator.guild_id}_{member_id}"
        self._attr_unique_id = f"{self._identifier}_{key}"
        self._attr_translation_key = key

    @property
    def device_info(self) -> DeviceInfo:
        member = self.coordinator.data[self.member_id]
        return DeviceInfo(
            identifiers={(DOMAIN, self._identifier)},
            name=member.display_name,
            manufacturer="Discord",
            model="Benutzer",
            via_device_id=self.coordinator.central_device_id,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return super().available and self.member_id in self.coordinator.data
