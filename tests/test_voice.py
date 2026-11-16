"""Bot control, TTS queue and native FFmpeg without real Discord connections."""

import asyncio
import io
import shutil
import subprocess
import wave
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.your_discord_connect.const import DOMAIN
from custom_components.your_discord_connect.gateway import DiscordGateway
from custom_components.your_discord_connect.voice import LEAVE_ALL, BotVoice, make_audio_source


@pytest.fixture
def voice_env(hass):
    guild = SimpleNamespace(
        voice_client=None, me=SimpleNamespace(voice=None), voice_channels=[], stage_channels=[]
    )
    permissions = SimpleNamespace(view_channel=True, connect=True, speak=True)
    voice = MagicMock()
    voice.channel = None
    voice.is_connected.side_effect = lambda: guild.voice_client is voice

    async def disconnect(**kwargs):
        guild.voice_client = None
        guild.me.voice = None

    async def move(channel, **kwargs):
        voice.channel = channel

    voice.disconnect = AsyncMock(side_effect=disconnect)
    voice.move_to = AsyncMock(side_effect=move)
    voice.play.side_effect = lambda source, after: hass.loop.call_soon(after, None)

    def channel(number, name, position=0):
        ch = SimpleNamespace(
            id=number,
            name=name,
            position=position,
            guild=guild,
            permissions_for=lambda member: permissions,
        )

        async def connect(**kwargs):
            guild.voice_client = voice
            voice.channel = ch
            guild.me.voice = SimpleNamespace(mute=False, suppress=False)
            return voice

        ch.connect = AsyncMock(side_effect=connect)
        return ch

    guild.voice_channels = [channel(10, "General"), channel(11, "General", 1)]
    guild.stage_channels = [channel(12, "Stage", 2)]
    fake_gateway = SimpleNamespace(
        guild=guild,
        connected=True,
        on_bot_update=None,
        channels=[*guild.voice_channels, *guild.stage_channels],
    )
    controller = BotVoice(hass, fake_gateway)
    return SimpleNamespace(
        controller=controller,
        gateway=fake_gateway,
        guild=guild,
        voice=voice,
        permissions=permissions,
    )


async def test_join_move_leave_and_duplicate_names(voice_env):
    c = voice_env.controller
    assert c.options == [LEAVE_ALL, "General (10)", "General (11)", "Stage (12)"]
    assert c.current_option == LEAVE_ALL
    await c.select("General (10)")
    voice_env.guild.voice_channels[0].connect.assert_awaited_once_with(
        timeout=20, reconnect=True, self_deaf=True
    )
    assert c.current_option == "General (10)"
    await c.select("General (11)")
    voice_env.voice.move_to.assert_awaited_once()
    assert c.current_option == "General (11)"
    await c.select(LEAVE_ALL)
    voice_env.voice.disconnect.assert_awaited_once_with(force=True)
    assert c.current_option == LEAVE_ALL


async def test_permission_failure_does_not_fake_selection(voice_env):
    voice_env.permissions.connect = False
    with pytest.raises(HomeAssistantError) as exc:
        await voice_env.controller.select("General (10)")
    assert exc.value.translation_key == "voice_permissions"
    assert voice_env.controller.current_option == LEAVE_ALL
    voice_env.guild.voice_channels[0].connect.assert_not_awaited()
    with pytest.raises(HomeAssistantError):
        await voice_env.controller.select("Missing (99)")


async def test_tts_plays_once_and_stays_in_selected_channel(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    c.set_text("Hello Discord")
    source = MagicMock()
    with (
        patch.object(c, "_render", new=AsyncMock(return_value=(b"audio", "ffmpeg"))) as render,
        patch(
            "custom_components.your_discord_connect.voice.make_audio_source", return_value=source
        ),
    ):
        await c.speak()
    render.assert_awaited_once_with("Hello Discord")
    voice_env.voice.play.assert_called_once()
    assert c.current_option == "General (10)"
    await c.async_close()
    assert c.current_option == LEAVE_ALL


async def test_stage_suppression_and_empty_text_are_errors(voice_env):
    c = voice_env.controller
    await c.select("Stage (12)")
    with pytest.raises(HomeAssistantError) as exc:
        await c.speak()
    assert exc.value.translation_key == "tts_invalid_text"
    c.set_text("Announcement")
    voice_env.guild.me.voice.suppress = True
    with pytest.raises(HomeAssistantError) as exc:
        await c.speak()
    assert exc.value.translation_key == "voice_cannot_speak"
    with pytest.raises(HomeAssistantError):
        c.set_text("x" * 256)
    await c.async_close()


async def test_channel_change_cancels_pending_tts_and_does_not_play_elsewhere(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    c.set_text("First")
    started = asyncio.Event()

    async def render(text):
        started.set()
        await asyncio.Event().wait()

    with patch.object(c, "_render", side_effect=render):
        first = asyncio.create_task(c.speak())
        await started.wait()
        c.set_text("Second")
        second = asyncio.create_task(c.speak())
        await asyncio.sleep(0)
        await c.select("General (11)")
        results = await asyncio.gather(first, second, return_exceptions=True)
    assert all(isinstance(result, HomeAssistantError) for result in results)
    assert not c._jobs
    voice_env.voice.play.assert_not_called()
    assert c.current_option == "General (11)"
    await c.async_close()


async def test_home_assistant_default_tts_is_used(hass, voice_env):
    c = voice_env.controller
    with pytest.raises(HomeAssistantError) as exc:
        await c._render("Hi")
    assert exc.value.translation_key == "tts_unavailable"
    hass.config.components.add("tts")
    with (
        patch("homeassistant.components.tts.async_default_engine", return_value="tts.piper"),
        patch(
            "homeassistant.components.tts.media_source.generate_media_source_id",
            return_value="media-source://tts/test",
        ) as generate,
        patch(
            "homeassistant.components.tts.async_get_media_source_audio",
            new=AsyncMock(return_value=("wav", b"audio")),
        ) as get_audio,
        patch(
            "homeassistant.components.ffmpeg.get_ffmpeg_manager",
            return_value=SimpleNamespace(binary="/usr/bin/ffmpeg"),
        ),
    ):
        assert await c._render("Hi") == (b"audio", "/usr/bin/ffmpeg")
    generate.assert_called_once_with(hass, "Hi", cache=False)
    get_audio.assert_awaited_once_with(hass, "media-source://tts/test")


@pytest.mark.parametrize("audio_format", ["wav", "mp3"])
async def test_native_ffmpeg_produces_opus_packets(hass, audio_format):
    import discord.voice_client

    assert discord.voice_client.has_nacl
    assert discord.voice_client.has_dave
    assert shutil.which("ffmpeg"), "FFmpeg is required for the voice development workflow"
    wav = io.BytesIO()
    with wave.open(wav, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\0\0" * 4800)

    def encode():
        audio = wav.getvalue()
        if audio_format == "mp3":
            audio = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "mp3", "pipe:1"],
                input=audio,
                capture_output=True,
                check=True,
                timeout=10,
            ).stdout
        source = make_audio_source(audio, "ffmpeg")
        try:
            packets = []
            while packet := source.read():
                packets.append(packet)
            assert source.is_opus()
            assert len(packets) >= 5
        finally:
            source.cleanup()

    await hass.async_add_executor_job(encode)


@pytest.mark.usefixtures("discord", "gateway")
async def test_bot_identity_filters_only_own_bot_and_entities_work(hass, entry, voice_env):
    with (
        patch.object(DiscordGateway, "bot_id", new_callable=PropertyMock, return_value="1"),
        patch.object(
            DiscordGateway, "bot_name", new_callable=PropertyMock, return_value="Test bot"
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        devices = dr.async_get(hass)
        assert devices.async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id) is None
        assert devices.async_get_device_by_identifier((DOMAIN, "100_2"), entry.entry_id)
        bot = devices.async_get_device_by_identifier((DOMAIN, "100_bot"), entry.entry_id)
        assert bot.config_subentry_id == entry.runtime_data.groups["central"]
        assert bot.name == "Bot: Test bot"
        assert len(entry.runtime_data.data) == 2  # Counts still include the bot.
        controller = entry.runtime_data.voice
        controller.gateway = voice_env.gateway
        controller.notify()
        select_id = registry.async_get_entity_id("select", DOMAIN, "100_bot_channel")
        text_id = registry.async_get_entity_id("text", DOMAIN, "100_tts_message")
        button_id = registry.async_get_entity_id("button", DOMAIN, "100_tts_execute")
        assert hass.states.get(select_id).attributes["options"][0] == LEAVE_ALL
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": select_id, "option": "General (10)"},
            blocking=True,
        )
        await hass.services.async_call(
            "text", "set_value", {"entity_id": text_id, "value": "Test announcement"}, blocking=True
        )
        assert hass.states.get(text_id).state == "Test announcement"
        with (
            patch.object(controller, "_render", new=AsyncMock(return_value=(b"audio", "ffmpeg"))),
            patch(
                "custom_components.your_discord_connect.voice.make_audio_source",
                return_value=MagicMock(),
            ),
        ):
            await hass.services.async_call(
                "button", "press", {"entity_id": button_id}, blocking=True
            )
        voice_env.voice.play.assert_called_once()
        await hass.services.async_call(
            "select", "select_option", {"entity_id": select_id, "option": LEAVE_ALL}, blocking=True
        )
        await hass.config_entries.async_unload(entry.entry_id)


async def test_channel_rename_preserves_selection_and_deletion_clears_it(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    voice_env.guild.voice_channels[0].name = "Renamed"
    c.notify()
    assert c.current_option == "Renamed (10)"
    voice_env.voice.move_to.assert_not_awaited()
    voice_env.gateway.channels = [
        channel for channel in voice_env.gateway.channels if channel.id != 10
    ]
    c.notify()
    assert c.current_option == LEAVE_ALL
    assert "Renamed (10)" not in c.options
    c.set_text("Cannot speak to deleted channel")
    with pytest.raises(HomeAssistantError):
        await c.speak()
    await c.async_close()


async def test_queue_is_bounded_and_leave_cancels_all(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    c.set_text("Queued")
    started = asyncio.Event()

    async def render(text):
        started.set()
        await asyncio.Event().wait()

    with patch.object(c, "_render", side_effect=render):
        jobs = [asyncio.create_task(c.speak()) for _ in range(5)]
        await started.wait()
        with pytest.raises(HomeAssistantError) as exc:
            await c.speak()
        assert exc.value.translation_key == "tts_queue_full"
        await c.select(LEAVE_ALL)
        results = await asyncio.gather(*jobs, return_exceptions=True)
    assert all(isinstance(result, HomeAssistantError) for result in results)
    assert not c._jobs
    voice_env.voice.play.assert_not_called()


async def test_tts_queue_preserves_text_and_order(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    callbacks = []
    playing = asyncio.Event()

    def play(source, after):
        callbacks.append(after)
        playing.set()

    voice_env.voice.play.side_effect = play
    with (
        patch.object(c, "_render", new=AsyncMock(return_value=(b"audio", "ffmpeg"))) as render,
        patch(
            "custom_components.your_discord_connect.voice.make_audio_source",
            return_value=MagicMock(),
        ),
    ):
        c.set_text("First")
        first = asyncio.create_task(c.speak())
        await playing.wait()
        playing.clear()
        c.set_text("Second")
        second = asyncio.create_task(c.speak())
        await asyncio.sleep(0)
        assert render.await_count == 1
        callbacks[0](None)
        await playing.wait()
        callbacks[1](None)
        await asyncio.gather(first, second)
        assert [call.args[0] for call in render.await_args_list] == ["First", "Second"]
    await c.async_close()


@pytest.mark.usefixtures("discord", "gateway")
async def test_bot_identity_late_resolution_removes_old_member_device(hass, entry, gateway):
    with (
        patch.object(
            DiscordGateway, "bot_id", new_callable=PropertyMock, return_value=None
        ) as identity,
        patch.object(
            DiscordGateway, "bot_name", new_callable=PropertyMock, return_value="Resolved bot"
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        devices = dr.async_get(hass)
        assert devices.async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id)
        identity.return_value = "1"
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        assert devices.async_get_device_by_identifier((DOMAIN, "100_1"), entry.entry_id) is None
        assert devices.async_get_device_by_identifier((DOMAIN, "100_2"), entry.entry_id)
        assert devices.async_get_device_by_identifier((DOMAIN, "100_bot"), entry.entry_id)
        assert gateway["channels"].await_count == 2
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert gateway["channels"].await_count == 3
        assert len(dr.async_entries_for_config_entry(devices, entry.entry_id)) == 3


async def test_leave_interrupts_active_playback(voice_env):
    c = voice_env.controller
    await c.select("General (10)")
    c.set_text("Speaking")
    playing = asyncio.Event()
    callbacks = []

    def play(source, after):
        callbacks.append(after)
        playing.set()

    voice_env.voice.play.side_effect = play
    with (
        patch.object(c, "_render", new=AsyncMock(return_value=(b"audio", "ffmpeg"))),
        patch(
            "custom_components.your_discord_connect.voice.make_audio_source",
            return_value=MagicMock(),
        ),
    ):
        job = asyncio.create_task(c.speak())
        await playing.wait()
        await c.select(LEAVE_ALL)
        with pytest.raises(HomeAssistantError) as exc:
            await job
        assert exc.value.translation_key == "tts_interrupted"
        callbacks[0](None)  # Late audio-thread completion must be harmless.
        await asyncio.sleep(0)
    assert c.current_option == LEAVE_ALL
    assert not c._jobs
    assert voice_env.voice.stop.called
