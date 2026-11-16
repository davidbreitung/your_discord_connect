"""Home Assistant fixtures with all Discord traffic mocked."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.your_discord_connect.api import Member
from custom_components.your_discord_connect.const import DOMAIN


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Enable loading this custom integration in real Home Assistant."""


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test server",
        unique_id="100",
        data={"guild_id": "100", "token": "test-token"},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def discord():
    with (
        patch(
            "custom_components.your_discord_connect.api.DiscordClient.guilds",
            new_callable=AsyncMock,
            return_value={"100": "Test server"},
        ) as guilds,
        patch(
            "custom_components.your_discord_connect.api.DiscordClient.guild_name",
            new_callable=AsyncMock,
            return_value="Test server",
        ) as guild_name,
        patch(
            "custom_components.your_discord_connect.api.DiscordClient.members",
            new_callable=AsyncMock,
            return_value={
                "1": Member("1", "Alice", "alice.real"),
                "2": Member("2", "Bob", "bob.real"),
            },
        ) as members,
    ):
        yield {"guilds": guilds, "guild_name": guild_name, "members": members}


@pytest.fixture
def gateway():
    from custom_components.your_discord_connect.gateway import MemberState

    with (
        patch(
            "custom_components.your_discord_connect.gateway.DiscordGateway.snapshot",
            new_callable=AsyncMock,
            return_value={
                "1": MemberState("online", True, "General"),
                "2": MemberState("offline", False, None),
            },
        ) as snapshot,
        patch(
            "custom_components.your_discord_connect.gateway.DiscordGateway.async_close",
            new_callable=AsyncMock,
        ) as close,
    ):
        yield {"snapshot": snapshot, "close": close}
