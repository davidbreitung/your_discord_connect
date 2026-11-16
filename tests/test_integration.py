"""Exercise actual HA platforms, registries, polling and lifecycle."""

from datetime import timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.your_discord_connect.api import DiscordAuthError, DiscordError, Member
from custom_components.your_discord_connect.const import DOMAIN
from custom_components.your_discord_connect.gateway import MemberState

pytestmark = pytest.mark.usefixtures("gateway")


def sensors(hass, entry):
    return [
        entity
        for entity in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
        if entity.unique_id.endswith("_display_name")
    ]


async def setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_members_sync(hass, entry, discord):
    await setup(hass, entry)
    assert entry.runtime_data.update_interval == timedelta(minutes=15)
    assert len(sensors(hass, entry)) == 2
    registry = dr.async_get(hass)
    alice = registry.async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id)
    assert alice.name == "Alice"
    alice_entity = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "100_1_display_name")
    assert hass.states.get(alice_entity).state == "Alice"
    discord["members"].return_value = {
        "1": Member("1", "Alice renamed"),
        "3": Member("3", "Charlie"),
    }
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(alice_entity).state == "Alice renamed"
    assert registry.async_get(alice.id).name == "Alice renamed"
    assert registry.async_get_device_by_identifier((DOMAIN, "100_2"), entry.entry_id) is None
    assert registry.async_get_device_by_identifier((DOMAIN, "100_3"), entry.entry_id) is not None
    assert len(sensors(hass, entry)) == 2
    # A departed member returning must be added again with the same unique ID.
    discord["members"].return_value["2"] = Member("2", "Bob")
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len(sensors(hass, entry)) == 3


async def test_failure_retains_members_and_recovers(hass, entry, discord):
    await setup(hass, entry)
    discord["members"].side_effect = DiscordError
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len(dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)) == 2
    assert all(hass.states.get(e.entity_id).state == "unavailable" for e in sensors(hass, entry))
    discord["members"].side_effect = None
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert {hass.states.get(e.entity_id).state for e in sensors(hass, entry)} == {"Alice", "Bob"}


async def test_restart_prunes_stale_members(hass, entry, discord):
    await setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    discord["members"].return_value = {"1": Member("1", "Alice")}
    await setup(hass, entry)
    assert len(sensors(hass, entry)) == 1
    assert len(dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)) == 1


async def test_empty_snapshot_removes_all_members(hass, entry, discord):
    await setup(hass, entry)
    discord["members"].return_value = {}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert not sensors(hass, entry)
    assert not dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    discord["members"].return_value = {"1": Member("1", "Alice")}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert len(sensors(hass, entry)) == 1


async def test_options_reload_and_poll(hass, entry, discord):
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"sync_interval": 30})
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval == timedelta(minutes=30)
    calls = discord["members"].await_count
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=31))
    await hass.async_block_till_done()
    assert discord["members"].await_count == calls + 1
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "error,state",
    [
        (DiscordError, ConfigEntryState.SETUP_RETRY),
        (DiscordAuthError, ConfigEntryState.SETUP_ERROR),
    ],
)
async def test_initial_failure(hass, entry, discord, error, state):
    discord["members"].side_effect = error
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is state
    assert not sensors(hass, entry)


async def test_servers_are_isolated_and_custom_device_names_preserved(hass, entry, discord):
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Other server",
        unique_id="200",
        data={"guild_id": "200", "token": "test-token"},
    )
    await setup(hass, entry)
    other.add_to_hass(hass)
    await setup(hass, other)
    registry = dr.async_get(hass)
    alice = registry.async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id)
    registry.async_update_device(alice.id, name_by_user="My custom name")
    discord["members"].return_value = {"1": Member("1", "Renamed")}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert registry.async_get(alice.id).name_by_user == "My custom name"
    assert registry.async_get(alice.id).name == "Renamed"
    assert len(sensors(hass, other)) == 2
    assert registry.async_get_device_by_identifier((DOMAIN, "200_2"), other.entry_id)


async def test_full_setup_from_http_responses(hass, aioclient_mock):
    from custom_components.your_discord_connect.const import API_BASE

    aioclient_mock.get(f"{API_BASE}/users/@me/guilds", json=[{"id": "100", "name": "My server"}])
    aioclient_mock.get(f"{API_BASE}/guilds/100", json={"id": "100", "name": "My server"})
    aioclient_mock.get(
        f"{API_BASE}/guilds/100/members",
        json=[{"user": {"id": "1", "username": "alice"}, "nick": "Alice on Discord"}],
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={"token": "test-token"}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"guild_id": "100"})
    await hass.async_block_till_done()
    entry = result["result"]
    assert entry.state is ConfigEntryState.LOADED
    entity = sensors(hass, entry)[0]
    assert hass.states.get(entity.entity_id).state == "Alice on Discord"
    assert (
        dr.async_get(hass).async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id).name
        == "Alice on Discord"
    )


def state(hass, key, domain="sensor", member="1"):
    entity_id = er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"100_{member}_{key}")
    return hass.states.get(entity_id).state


async def test_all_member_entities_and_manual_sync(hass, entry, discord, gateway):
    await setup(hass, entry)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(entities) == 11  # Five per member and one server synchronization button.
    assert state(hass, "username") == "alice.real"
    assert state(hass, "presence") == "online"
    assert state(hass, "in_voice_channel", "binary_sensor") == "on"
    assert state(hass, "voice_channel") == "General"
    assert state(hass, "presence", member="2") == "offline"
    assert state(hass, "in_voice_channel", "binary_sensor", "2") == "off"
    assert state(hass, "voice_channel", member="2") == "unknown"
    # A cache change alone must not publish a new entity state.
    gateway["snapshot"].return_value = {"1": MemberState("idle", False, None)}
    assert state(hass, "presence") == "online"
    button = er.async_get(hass).async_get_entity_id("button", DOMAIN, "100_sync")
    assert hass.states.get(button).attributes["friendly_name"] == "Synchronize Test server"
    calls = discord["members"].await_count
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    await hass.async_block_till_done()
    assert discord["members"].await_count == calls + 1
    assert state(hass, "presence") == "idle"
    assert state(hass, "in_voice_channel", "binary_sensor") == "off"
    assert state(hass, "voice_channel") == "unknown"
    # A missing gateway member is unknown, never inferred offline or disconnected.
    assert state(hass, "presence", member="2") == "unknown"
    assert state(hass, "in_voice_channel", "binary_sensor", "2") == "unknown"


async def test_gateway_failure_preserves_devices_and_button(hass, entry, discord, gateway):
    await setup(hass, entry)
    discord["members"].return_value = {}
    gateway["snapshot"].side_effect = DiscordError("Gateway unavailable")
    button = er.async_get(hass).async_get_entity_id("button", DOMAIN, "100_sync")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    await hass.async_block_till_done()
    assert len(dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)) == 2
    assert state(hass, "presence") == "unavailable"
    assert hass.states.get(button).state != "unavailable"


async def test_all_member_entities_removed_but_button_survives(hass, entry, discord):
    await setup(hass, entry)
    discord["members"].return_value = {}
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert [entity.unique_id for entity in entities] == ["100_sync"]


async def test_unload_and_initial_failure_close_gateway(hass, entry, discord, gateway):
    await setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    gateway["close"].assert_awaited_once()
    gateway["close"].reset_mock()
    gateway["snapshot"].side_effect = DiscordError("Gateway unavailable")
    assert not await hass.config_entries.async_setup(entry.entry_id)
    gateway["close"].assert_awaited_once()
