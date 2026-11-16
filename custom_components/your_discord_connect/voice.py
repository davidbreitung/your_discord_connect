"""Bot channel control and bounded TTS playback through Home Assistant."""

import asyncio
import io
import os
from functools import partial

import discord
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

LEAVE_ALL = "alle verlassen"
MAX_TEXT_LENGTH = 255
MAX_QUEUE = 5


def voice_error(key):
    return HomeAssistantError(translation_domain=DOMAIN, translation_key=key)


def make_audio_source(audio: bytes, executable: str):
    """Decode only generated audio from stdin; no arbitrary media URLs or shell."""
    # discord.py expects a file object for stderr, not subprocess.DEVNULL.
    # Newer FFmpeg builds resolve '-' to fd rather than pipe; both are local only.
    with open(os.devnull, "wb") as stderr:
        source = discord.FFmpegOpusAudio(
            io.BytesIO(audio),
            executable=executable,
            pipe=True,
            bitrate=64,
            before_options="-nostdin -protocol_whitelist pipe,fd",
            options="-vn",
            stderr=stderr,
        )
    return source


class BotVoice:
    def __init__(self, hass, gateway):
        self.hass = hass
        self.gateway = gateway
        self.text = ""
        self._listeners = set()
        self._connection_lock = asyncio.Lock()
        self._speech_lock = asyncio.Lock()
        self._jobs = set()
        self._closing = False
        self._observed_channel = None
        gateway.on_bot_update = self.notify

    @property
    def voice_client(self):
        guild = self.gateway.guild
        return guild.voice_client if guild else None

    @property
    def current_channel_id(self):
        voice = self.voice_client
        if voice and voice.is_connected() and voice.channel:
            if any(channel.id == voice.channel.id for channel in self.gateway.channels):
                return voice.channel.id
        return None

    @property
    def channels(self):
        return sorted(self.gateway.channels, key=lambda c: (c.position, c.id))

    @property
    def options(self):
        return [LEAVE_ALL, *(f"{channel.name} ({channel.id})" for channel in self.channels)]

    @property
    def current_option(self):
        channel_id = self.current_channel_id
        return next((f"{c.name} ({c.id})" for c in self.channels if c.id == channel_id), LEAVE_ALL)

    def add_listener(self, listener):
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def notify(self):
        current = self.current_channel_id
        if current != self._observed_channel or not self.gateway.connected:
            for task in tuple(self._jobs):
                if not task.cancelling():
                    task.cancel()
            if voice := self.voice_client:
                voice.stop()
        self._observed_channel = current
        for listener in tuple(self._listeners):
            listener()

    async def _cancel_jobs(self):
        tasks = tuple(self._jobs)
        for task in tasks:
            if not task.cancelling():
                task.cancel()
        if voice := self.voice_client:
            voice.stop()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def select(self, option):
        target = next((c for c in self.channels if f"{c.name} ({c.id})" == option), None)
        if option != LEAVE_ALL and target is None:
            raise voice_error("voice_channel_missing")
        if target:
            if not self.gateway.connected:
                raise voice_error("voice_not_ready")
            permissions = target.permissions_for(target.guild.me)
            if not permissions.view_channel or not permissions.connect:
                raise voice_error("voice_permissions")
            if target.id == self.current_channel_id:
                return
        await self._cancel_jobs()
        async with self._connection_lock:
            if self._closing:
                raise voice_error("voice_not_ready")
            voice = self.voice_client
            try:
                if target is None:
                    if voice:
                        await voice.disconnect(force=True)
                elif voice and voice.is_connected():
                    if voice.channel.id != target.id:
                        await voice.move_to(target, timeout=20)
                else:
                    if voice:
                        await voice.disconnect(force=True)
                    await target.connect(timeout=20, reconnect=True, self_deaf=True)
            except (discord.DiscordException, TimeoutError, OSError, RuntimeError) as err:
                if (voice := self.voice_client) and not voice.is_connected():
                    await voice.disconnect(force=True)
                raise voice_error("voice_connection_failed") from err
            finally:
                self.notify()

    def set_text(self, text):
        if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
            raise voice_error("tts_invalid_text")
        self.text = text
        for listener in tuple(self._listeners):
            listener()

    async def _render(self, text):
        if "tts" not in self.hass.config.components:
            raise voice_error("tts_unavailable")
        # Lazy imports keep member synchronization usable without a TTS provider.
        from homeassistant.components import tts
        from homeassistant.components.ffmpeg import get_ffmpeg_manager
        from homeassistant.components.tts.media_source import generate_media_source_id

        if tts.async_default_engine(self.hass) is None:
            raise voice_error("tts_unavailable")
        media_id = generate_media_source_id(self.hass, text, cache=False)
        try:
            async with asyncio.timeout(60):
                _, audio = await tts.async_get_media_source_audio(self.hass, media_id)
            executable = get_ffmpeg_manager(self.hass).binary
        except (HomeAssistantError, ValueError, TimeoutError) as err:
            raise voice_error("tts_generation_failed") from err
        if not audio or len(audio) > 10 * 1024 * 1024:
            raise voice_error("tts_generation_failed")
        return audio, executable

    async def speak(self):
        text = self.text
        channel_id = self.current_channel_id
        if not text.strip():
            raise voice_error("tts_invalid_text")
        if self._closing or not self.gateway.connected or channel_id is None:
            raise voice_error("voice_not_ready")
        if len(self._jobs) >= MAX_QUEUE:
            raise voice_error("tts_queue_full")
        task = self.hass.async_create_background_task(
            self._speak(text, channel_id), "your_discord_connect TTS"
        )
        self._jobs.add(task)
        try:
            await task
        except asyncio.CancelledError as err:
            raise voice_error("tts_interrupted") from err
        finally:
            self._jobs.discard(task)

    async def _speak(self, text, channel_id):
        async with self._speech_lock:
            self._validate_playback(channel_id)
            audio, executable = await self._render(text)
            self._validate_playback(channel_id)
            # Subprocess creation is blocking and must not run on HA's event loop.
            creation = self.hass.async_add_executor_job(
                partial(make_audio_source, audio, executable)
            )
            try:
                source = await asyncio.shield(creation)
            except asyncio.CancelledError:
                source = await creation
                await self.hass.async_add_executor_job(source.cleanup)
                raise
            except (discord.DiscordException, OSError) as err:
                raise voice_error("tts_ffmpeg_failed") from err
            voice = self.voice_client
            done = self.hass.loop.create_future()

            def finish(error):
                if not done.done():
                    if error:
                        done.set_exception(voice_error("tts_playback_failed"))
                    else:
                        done.set_result(None)

            def after(error):
                self.hass.loop.call_soon_threadsafe(finish, error)

            started = False
            try:
                self._validate_playback(channel_id)
                voice.play(source, after=after)
                started = True
                async with asyncio.timeout(120):
                    await done
            except (discord.DiscordException, TimeoutError) as err:
                raise voice_error("tts_playback_failed") from err
            finally:
                if started:
                    voice.stop()  # discord.py's audio thread owns source cleanup.
                else:
                    await self.hass.async_add_executor_job(source.cleanup)

    def _validate_playback(self, channel_id):
        if self._closing or not self.gateway.connected or self.current_channel_id != channel_id:
            raise voice_error("voice_not_ready")
        guild = self.gateway.guild
        voice = guild.me.voice
        if voice and (voice.mute or voice.suppress):
            raise voice_error("voice_cannot_speak")
        if not self.voice_client.channel.permissions_for(guild.me).speak:
            raise voice_error("voice_permissions")

    async def async_close(self):
        self._closing = True
        self.gateway.on_bot_update = None
        await self._cancel_jobs()
        async with self._connection_lock:
            if voice := self.voice_client:
                await voice.disconnect(force=True)
