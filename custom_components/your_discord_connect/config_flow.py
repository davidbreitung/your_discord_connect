"""UI setup, central options and token reauthentication."""

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    DiscordAuthError,
    DiscordClient,
    DiscordError,
    DiscordNotFoundError,
    DiscordPermissionError,
    DiscordRateLimitError,
)
from .const import (
    CONF_GUILD_ID,
    CONF_SYNC_INTERVAL,
    DEFAULT_SYNC_INTERVAL,
    DOMAIN,
    MAX_SYNC_INTERVAL,
)

TOKEN_SCHEMA = vol.Schema(
    {vol.Required(CONF_TOKEN): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))}
)


def error_key(err: DiscordError) -> str:
    if isinstance(err, DiscordAuthError):
        return "invalid_auth"
    if isinstance(err, DiscordPermissionError):
        return "missing_permissions"
    if isinstance(err, DiscordNotFoundError):
        return "server_not_found"
    if isinstance(err, DiscordRateLimitError):
        return "rate_limited"
    return "cannot_connect"


class DiscordConfigFlow(ConfigFlow, domain=DOMAIN):
    """Discover servers and validate member access before creating an entry."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DiscordOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._token = user_input[CONF_TOKEN].strip()
            self._client = DiscordClient(async_get_clientsession(self.hass), self._token)
            try:
                self._guilds = await self._client.guilds()
            except DiscordError as err:
                errors["base"] = error_key(err)
            else:
                if self._guilds:
                    return await self.async_step_guild()
                errors["base"] = "no_servers"
        return self.async_show_form(step_id="user", data_schema=TOKEN_SCHEMA, errors=errors)

    async def async_step_guild(self, user_input=None):
        errors = {}
        if user_input is not None:
            guild_id = user_input[CONF_GUILD_ID]
            if guild_id not in self._guilds:
                errors["base"] = "server_not_found"
            else:
                await self.async_set_unique_id(guild_id)
                self._abort_if_unique_id_configured()
                try:
                    name = await self._client.guild_name(guild_id)
                    await self._client.members(guild_id)
                except DiscordError as err:
                    errors["base"] = error_key(err)
                else:
                    return self.async_create_entry(
                        title=name, data={CONF_TOKEN: self._token, CONF_GUILD_ID: guild_id}
                    )
        return self.async_show_form(
            step_id="guild",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GUILD_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {"value": key, "label": f"{name} ({key})"}
                                for key, name in self._guilds.items()
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            entry = self._get_reauth_entry()
            client = DiscordClient(async_get_clientsession(self.hass), token)
            try:
                await client.members(entry.data[CONF_GUILD_ID])
            except DiscordError as err:
                errors["base"] = error_key(err)
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: token})
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=TOKEN_SCHEMA, errors=errors
        )


class DiscordOptionsFlow(OptionsFlow):
    """Configure one synchronization interval for all members of this server."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            interval = user_input[CONF_SYNC_INTERVAL]
            if interval != int(interval) or not 1 <= interval <= MAX_SYNC_INTERVAL:
                errors[CONF_SYNC_INTERVAL] = "invalid_interval"
            else:
                return self.async_create_entry(title="", data={CONF_SYNC_INTERVAL: int(interval)})
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SYNC_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=MAX_SYNC_INTERVAL,
                            step=1,
                            unit_of_measurement="min",
                            mode=NumberSelectorMode.BOX,
                        )
                    )
                }
            ),
            errors=errors,
        )
