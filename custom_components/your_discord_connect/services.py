"""Public interface for automations and other integrations."""

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .api import (
    DiscordAuthError,
    DiscordError,
    DiscordPermissionError,
    DiscordRateLimitError,
)
from .const import DOMAIN

SERVICE_SEND_DIRECT_MESSAGE = "send_direct_message"


async def async_send_direct_message(
    hass: HomeAssistant, device_id: str, content: str
) -> dict[str, str]:
    """Send text to an existing member device; return Discord message/recipient IDs.

    Raises ServiceValidationError for invalid destinations or text, and
    HomeAssistantError for Discord failures. Callers need no bot token.
    """
    if not isinstance(content, str) or not content.strip() or len(content) > 2000:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_message")
    if not isinstance(device_id, str):
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_recipient")
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_recipient")
    entry = hass.config_entries.async_get_entry(device.config_entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_recipient")
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="entry_not_ready")
    coordinator = entry.runtime_data
    member_id = next(
        (
            key
            for key in coordinator.data
            if (DOMAIN, f"{coordinator.guild_id}_{key}") in device.identifiers
        ),
        None,
    )
    if member_id is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_recipient")
    try:
        return await coordinator.client.send_direct_message(member_id, content)
    except DiscordAuthError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="dm_invalid_auth"
        ) from err
    except DiscordPermissionError as err:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="dm_forbidden") from err
    except DiscordRateLimitError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="dm_rate_limited"
        ) from err
    except DiscordError as err:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="dm_failed") from err


@callback
def async_register_services(hass: HomeAssistant) -> None:
    async def send(call):
        return await async_send_direct_message(hass, call.data["device_id"], call.data["content"])

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_DIRECT_MESSAGE,
        send,
        schema=vol.Schema(
            {vol.Required("device_id"): cv.string, vol.Required("content"): cv.string}
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
