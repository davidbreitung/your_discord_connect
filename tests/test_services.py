"""Public DM interface with real HA service dispatch and simulated Discord HTTP."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service import async_get_all_descriptions

from custom_components.your_discord_connect.const import API_BASE, DOMAIN
from custom_components.your_discord_connect.services import async_send_direct_message

pytestmark = pytest.mark.usefixtures("gateway", "discord")


async def member_device(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return dr.async_get(hass).async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id)


async def test_send_service_and_public_function(hass, entry, aioclient_mock):
    member = await member_device(hass, entry)
    aioclient_mock.post(f"{API_BASE}/users/@me/channels", json={"id": "500"})
    aioclient_mock.post(f"{API_BASE}/channels/500/messages", json={"id": "600"})
    result = await hass.services.async_call(
        DOMAIN,
        "send_direct_message",
        {"device_id": member.id, "content": "Hello"},
        blocking=True,
        return_response=True,
    )
    assert result == {"message_id": "600", "recipient_id": "1"}
    assert aioclient_mock.mock_calls[0][2] == {"recipient_id": "1"}
    assert aioclient_mock.mock_calls[1][2] == {
        "content": "Hello",
        "allowed_mentions": {"parse": []},
    }
    assert aioclient_mock.mock_calls[1][3]["Authorization"] == "Bot test-token"
    assert await async_send_direct_message(hass, member.id, "Second") == result
    descriptions = await async_get_all_descriptions(hass)
    assert descriptions[DOMAIN]["send_direct_message"]["fields"]["device_id"]["required"]


@pytest.mark.parametrize("content", ["", "   ", "x" * 2001, None])
async def test_invalid_content_never_sends(hass, entry, content, aioclient_mock):
    member = await member_device(hass, entry)
    with pytest.raises(ServiceValidationError):
        await async_send_direct_message(hass, member.id, content)
    assert aioclient_mock.call_count == 0


async def test_unknown_central_and_unloaded_devices_rejected(hass, entry, aioclient_mock):
    member = await member_device(hass, entry)
    central = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, "100_central"), entry.entry_id
    )
    for device_id in ("missing", central.id):
        with pytest.raises(ServiceValidationError):
            await async_send_direct_message(hass, device_id, "Hello")
    await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError):
        await async_send_direct_message(hass, member.id, "Hello")
    assert aioclient_mock.call_count == 0


@pytest.mark.parametrize(
    "status,key",
    [(401, "dm_invalid_auth"), (403, "dm_forbidden"), (429, "dm_rate_limited"), (500, "dm_failed")],
)
async def test_discord_error_is_clear_and_not_retried(hass, entry, aioclient_mock, status, key):
    member = await member_device(hass, entry)
    aioclient_mock.post(f"{API_BASE}/users/@me/channels", json={"id": "500"})
    aioclient_mock.post(f"{API_BASE}/channels/500/messages", status=status)
    with pytest.raises(HomeAssistantError) as error:
        await async_send_direct_message(hass, member.id, "Hello")
    assert error.value.translation_key == key
    assert aioclient_mock.call_count == 2


async def test_multiple_servers_use_selected_devices_bot(hass, entry):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    await member_device(hass, entry)
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Other",
        unique_id="200",
        data={"guild_id": "200", "token": "other-test-token"},
    )
    other.add_to_hass(hass)
    assert await hass.config_entries.async_setup(other.entry_id)
    await hass.async_block_till_done()
    member = dr.async_get(hass).async_get_device_by_identifier((DOMAIN, "200_1"), other.entry_id)
    with (
        patch.object(
            entry.runtime_data.client, "send_direct_message", new_callable=AsyncMock
        ) as first,
        patch.object(
            other.runtime_data.client,
            "send_direct_message",
            new_callable=AsyncMock,
            return_value={"message_id": "600", "recipient_id": "1"},
        ) as second,
    ):
        await async_send_direct_message(hass, member.id, "Hello")
        first.assert_not_awaited()
        second.assert_awaited_once_with("1", "Hello")
