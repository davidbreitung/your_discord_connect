"""Managed Discord gateway for presence and voice state snapshots."""

import asyncio
from dataclasses import dataclass

import discord
from homeassistant.core import HomeAssistant

from .api import DiscordAuthError, DiscordError, DiscordPermissionError


@dataclass(frozen=True)
class MemberState:
    """Values captured at synchronization time, not live entity updates."""

    presence: str
    in_voice_channel: bool
    voice_channel: str | None


class DiscordGateway:
    """Let discord.py handle heartbeats, session resumes and reconnect backoff."""

    def __init__(self, hass: HomeAssistant, token: str, guild_id: str) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        intents.presences = True
        intents.voice_states = True
        self._client = discord.Client(intents=intents, chunk_guilds_at_startup=False)
        self._hass = hass
        self._token = token
        self._guild_id = int(guild_id)
        self._ready = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._error: DiscordError | None = None

        @self._client.event
        async def on_ready():
            self._ready.set()

        @self._client.event
        async def on_resumed():
            self._ready.set()

        @self._client.event
        async def on_disconnect():
            self._ready.clear()

    async def _run(self) -> None:
        try:
            async with self._client:
                await self._client.start(self._token, reconnect=True)
        except discord.LoginFailure:
            self._error = DiscordAuthError("Discord bot token is no longer valid")
        except discord.PrivilegedIntentsRequired:
            self._error = DiscordPermissionError(
                "Enable Server Members Intent and Presence Intent in the Discord Developer Portal, "
                "then reload the integration"
            )
        except Exception:
            # Do not expose tokens, request headers or member data in errors.
            self._error = DiscordError("Discord gateway connection failed; reload the integration")
        finally:
            self._ready.set()

    async def snapshot(self, member_ids: list[str]) -> dict[str, MemberState]:
        if self._task is None:
            self._task = self._hass.async_create_background_task(
                self._run(), "your_discord_connect gateway"
            )
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=60)
        except TimeoutError as err:
            raise DiscordError("Discord gateway is not ready") from err
        if self._error:
            raise self._error
        if self._task.done() or not self._client.is_ready():
            raise DiscordError("Discord gateway is disconnected")
        guild = self._client.get_guild(self._guild_id)
        if guild is None or guild.unavailable:
            raise DiscordError("Discord server is unavailable on the gateway")

        result = {}
        try:
            # A regular member chunk does not request presences. Query explicit IDs
            # with presences=True (Discord permits at most 100 IDs per request).
            for offset in range(0, len(member_ids), 100):
                members = await guild.query_members(
                    user_ids=[int(value) for value in member_ids[offset : offset + 100]],
                    presences=True,
                    cache=True,
                )
                for member in members:
                    voice = member.voice
                    channel = voice.channel if voice else None
                    result[str(member.id)] = MemberState(
                        presence=str(member.status),
                        in_voice_channel=voice is not None,
                        voice_channel=channel.name if channel else None,
                    )
        except (discord.DiscordException, TimeoutError) as err:
            raise DiscordError("Cannot synchronize Discord presence and voice states") from err
        if not self._client.is_ready() or not self._ready.is_set() or guild.unavailable:
            raise DiscordError("Discord gateway disconnected during synchronization")
        return result

    async def async_close(self) -> None:
        await self._client.close()
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
