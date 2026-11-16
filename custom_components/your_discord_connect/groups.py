"""Persistent Home Assistant groups and a central server device."""

from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

CENTRAL_KEYS = ("member_count", "online_count", "voice_count")


def central_device_info(guild_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{guild_id}_central")},
        name="zentrale Konfiguration",
        manufacturer="Discord",
        model="zentrale Konfiguration",
        entry_type=dr.DeviceEntryType.SERVICE,
    )


def setup_groups(hass, entry, coordinator):
    """Add fixed subentries once; preserve their IDs and user device settings."""
    groups = {}
    for key, title in (("central", "zentrale Konfiguration"), ("users", "Benutzer")):
        subentry = next((s for s in entry.subentries.values() if s.unique_id == key), None)
        if subentry is None:
            subentry = ConfigSubentry(
                data=MappingProxyType({}), subentry_type=key, title=title, unique_id=key
            )
            hass.config_entries.async_add_subentry(entry, subentry)
        groups[key] = subentry.subentry_id
    coordinator.groups = groups
    registry = dr.async_get(hass)
    central = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        config_subentry_id=groups["central"],
        **central_device_info(coordinator.guild_id),
    )
    coordinator.central_device_id = central.id
    bot = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        config_subentry_id=groups["central"],
        **bot_device_info(coordinator),
    )
    # Move existing member devices without replacing IDs, areas or custom names.
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if device.id not in (central.id, bot.id):
            registry.async_update_device(
                device.id,
                new_config_subentry_id=groups["users"],
                model="Benutzer",
                via_device_id=central.id,
            )


def bot_device_info(coordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{coordinator.guild_id}_bot")},
        name=f"Bot: {coordinator.gateway.bot_name}",
        manufacturer="Discord",
        model="Bot",
        via_device_id=coordinator.central_device_id,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
