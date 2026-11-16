"""Direct messages require an explicit button press and keep drafts on failure."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.your_discord_connect.api import DiscordPermissionError
from custom_components.your_discord_connect.const import DOMAIN

pytestmark = pytest.mark.usefixtures("discord", "gateway")


async def test_draft_and_explicit_send(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    text = registry.async_get_entity_id("text", DOMAIN, "100_1_private_message")
    button = registry.async_get_entity_id("button", DOMAIN, "100_1_private_message_send")
    with patch.object(entry.runtime_data.client, "send_direct_message", new=AsyncMock()) as send:
        await hass.services.async_call(
            "text", "set_value", {"entity_id": text, "value": "Hello Alice"}, blocking=True
        )
        send.assert_not_awaited()
        assert hass.states.get(text).state == "Hello Alice"
        await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
        send.assert_awaited_once_with("1", "Hello Alice")
        assert hass.states.get(text).state == ""
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
        assert send.await_count == 1


async def test_failure_retains_draft_and_reload_clears(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    text = registry.async_get_entity_id("text", DOMAIN, "100_1_private_message")
    button = registry.async_get_entity_id("button", DOMAIN, "100_1_private_message_send")
    await hass.services.async_call(
        "text", "set_value", {"entity_id": text, "value": "Test"}, blocking=True
    )
    with patch.object(
        entry.runtime_data.client, "send_direct_message", side_effect=DiscordPermissionError
    ):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
        assert hass.states.get(text).state == "Test"
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(text).state == ""


async def test_inflight_send_preserves_new_draft_and_blocks_duplicate(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    text = registry.async_get_entity_id("text", DOMAIN, "100_1_private_message")
    button = registry.async_get_entity_id("button", DOMAIN, "100_1_private_message_send")
    await hass.services.async_call(
        "text", "set_value", {"entity_id": text, "value": "First"}, blocking=True
    )
    started, finish = asyncio.Event(), asyncio.Event()

    async def send(*args):
        started.set()
        await finish.wait()

    with patch.object(entry.runtime_data.client, "send_direct_message", side_effect=send) as mock:
        task = asyncio.create_task(
            hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
        )
        await started.wait()
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
        await hass.services.async_call(
            "text", "set_value", {"entity_id": text, "value": "Next"}, blocking=True
        )
        finish.set()
        await task
        mock.assert_awaited_once_with("1", "First")
    assert hass.states.get(text).state == "Next"
