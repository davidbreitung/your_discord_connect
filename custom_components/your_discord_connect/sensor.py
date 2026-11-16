"""Represent each server member by a device and display-name sensor."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DiscordConfigEntry
from .const import DOMAIN
from .coordinator import DiscordCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: DiscordConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()
    devices = dr.async_get(hass)
    entities = er.async_get(hass)

    @callback
    def reconcile_members() -> None:
        if not coordinator.last_update_success:
            return
        current = coordinator.data
        prefix = f"{coordinator.guild_id}_"
        valid_ids = {f"{prefix}{member_id}" for member_id in current}
        valid_entity_ids = {f"{identifier}_display_name" for identifier in valid_ids}
        # Registry cleanup also handles members who left while Home Assistant was stopped.
        for entity in er.async_entries_for_config_entry(entities, entry.entry_id):
            if entity.platform == DOMAIN and entity.unique_id not in valid_entity_ids:
                entities.async_remove(entity.entity_id)
        for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
            identifiers = {
                identifier for domain, identifier in device.identifiers if domain == DOMAIN
            }
            if identifiers and not identifiers.intersection(valid_ids):
                devices.async_remove_device(device.id)
        new = set(current) - known
        known.intersection_update(current)
        known.update(new)
        async_add_entities(DiscordMemberSensor(coordinator, member_id) for member_id in sorted(new))
        for member_id, member in current.items():
            if device := devices.async_get_device_by_identifier(
                (DOMAIN, f"{prefix}{member_id}"), entry.entry_id
            ):
                if device.name != member.display_name:
                    devices.async_update_device(device.id, name=member.display_name)

    entry.async_on_unload(coordinator.async_add_listener(reconcile_members))
    reconcile_members()


class DiscordMemberSensor(CoordinatorEntity[DiscordCoordinator], SensorEntity):
    """Stable Discord IDs prevent duplicates when a member changes their name."""

    _attr_has_entity_name = True
    _attr_translation_key = "display_name"
    _attr_icon = "mdi:account"

    def __init__(self, coordinator: DiscordCoordinator, member_id: str) -> None:
        super().__init__(coordinator)
        self.member_id = member_id
        self._identifier = f"{coordinator.guild_id}_{member_id}"
        self._attr_unique_id = f"{self._identifier}_display_name"

    @property
    def device_info(self) -> DeviceInfo:
        member = self.coordinator.data[self.member_id]
        return DeviceInfo(
            identifiers={(DOMAIN, self._identifier)},
            name=member.display_name,
            manufacturer="Discord",
            model="Server member",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        member = self.coordinator.data.get(self.member_id)
        return member.display_name if member else None

    @property
    def available(self) -> bool:
        return super().available and self.member_id in self.coordinator.data
