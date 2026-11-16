"""Exercise UI setup, errors, options and reauthentication."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.your_discord_connect.api import (
    DiscordAuthError,
    DiscordError,
    DiscordNotFoundError,
    DiscordPermissionError,
    DiscordRateLimitError,
)
from custom_components.your_discord_connect.const import DOMAIN


async def start(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"token": "test-token"}
    )


async def test_setup(hass, discord):
    result = await start(hass)
    assert result["step_id"] == "guild"
    with patch(
        "custom_components.your_discord_connect.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"guild_id": "100"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test server"
    assert result["data"] == {"guild_id": "100", "token": "test-token"}
    assert result["result"].unique_id == "100"
    discord["members"].assert_awaited_once_with("100")


@pytest.mark.parametrize(
    "exception,key",
    [
        (DiscordAuthError, "invalid_auth"),
        (DiscordError, "cannot_connect"),
        (DiscordRateLimitError, "rate_limited"),
    ],
)
async def test_token_error(hass, discord, exception, key):
    discord["guilds"].side_effect = exception
    result = await start(hass)
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": key}


async def test_no_servers(hass, discord):
    discord["guilds"].return_value = {}
    result = await start(hass)
    assert result["errors"] == {"base": "no_servers"}


@pytest.mark.parametrize(
    "exception,key",
    [
        (DiscordPermissionError, "missing_permissions"),
        (DiscordNotFoundError, "server_not_found"),
        (DiscordError, "cannot_connect"),
    ],
)
async def test_member_access_required(hass, discord, exception, key):
    discord["members"].side_effect = exception
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"guild_id": "100"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": key}
    assert not hass.config_entries.async_entries(DOMAIN)


async def test_duplicate(hass, entry, discord):
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"guild_id": "100"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"sync_interval": 30}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"sync_interval": 30}


async def test_fractional_interval_rejected(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"sync_interval": 1.5}
    )
    assert result["errors"] == {"sync_interval": "invalid_interval"}


async def test_reauth(hass, entry, discord):
    result = await entry.start_reauth_flow(hass)
    with patch.object(hass.config_entries, "async_reload", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"token": "new-token"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["token"] == "new-token"
