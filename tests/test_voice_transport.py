"""Exercise real Opus/packet crypto with a fake UDP socket, never contacting Discord."""

import asyncio
import ctypes.util
import math
import struct
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import audioop
import discord
import nacl.secret
import pytest

from custom_components.your_discord_connect.voice_transport import (
    MeasuredConnectionState,
    MeasuredVoiceClient,
    VoiceEncryptionNotReady,
)


@pytest.fixture
def transport():
    if not discord.opus.is_loaded():
        discord.opus.load_opus(ctypes.util.find_library("opus"))
    # Bypass network lifecycle only; real send_audio_packet, Opus, packet encryption,
    # send_packet and diagnostics methods run unchanged.
    client = MeasuredVoiceClient.__new__(MeasuredVoiceClient)
    state = MeasuredConnectionState.__new__(MeasuredConnectionState)
    state.socket = MagicMock()
    state.secret_key = list(range(32))
    state.ssrc = 123
    state.mode = "aead_xchacha20_poly1305_rtpsize"
    state.dave_protocol_version = 0
    state.dave_session = None
    client._connection = state
    client.sequence = client.timestamp = client._incr_nonce = 0
    client.encoder = discord.opus.Encoder()
    client.reset_diagnostics()
    pcm = b"".join(
        struct.pack("<hh", sample, sample)
        for i in range(960)
        for sample in [int(8000 * math.sin(2 * math.pi * 440 * i / 48000))]
    )
    return client, state, pcm


def test_pcm_reaches_socket_as_decryptable_audible_opus(transport):
    client, state, pcm = transport
    client.send_audio_packet(pcm)
    packet = bytes(state.socket.sendall.call_args.args[0])
    header = packet[:12]
    nonce = packet[-4:] + bytes(20)
    opus = nacl.secret.Aead(bytes(state.secret_key)).decrypt(packet[12:-4], header, nonce)
    decoded = discord.opus.Decoder().decode(opus, fec=False)
    assert audioop.rms(decoded, 2) > 1000
    assert client.diagnostics() == {
        "last_voice_packets_submitted": 1,
        "last_voice_send_errors": 0,
        "last_dave_unready_packets": 0,
        "last_dave_protocol": 0,
    }


def test_socket_failure_is_counted_even_when_discord_swallows_it(transport):
    client, state, pcm = transport
    state.socket.sendall.side_effect = OSError("simulated UDP failure")
    client.send_audio_packet(pcm)  # discord.py suppresses the socket error.
    assert client.diagnostics()["last_voice_send_errors"] == 1
    assert client.diagnostics()["last_voice_packets_submitted"] == 0
    client.reset_diagnostics()
    assert client.diagnostics()["last_voice_send_errors"] == 0
    assert client.diagnostics()["last_dave_protocol"] is None


def test_unready_dave_blocks_packets_without_disabling_encryption(transport):
    client, state, pcm = transport
    state.dave_protocol_version = 1
    state.dave_session = SimpleNamespace(ready=False, encrypt_opus=MagicMock(return_value=b"dave"))
    with pytest.raises(VoiceEncryptionNotReady):
        client.send_audio_packet(pcm)
    state.socket.sendall.assert_not_called()
    state.dave_session.encrypt_opus.assert_not_called()
    assert client.diagnostics()["last_dave_unready_packets"] == 1
    state.dave_session.ready = True
    client.send_audio_packet(pcm)
    state.dave_session.encrypt_opus.assert_called_once()
    assert client.diagnostics()["last_voice_packets_submitted"] == 1
    assert client.diagnostics()["last_dave_unready_packets"] == 1
    assert client.diagnostics()["last_dave_protocol"] == 1


def test_connection_factory_preserves_library_lifecycle_initialization():
    client = MeasuredVoiceClient.__new__(MeasuredVoiceClient)
    # Avoid the socket reader thread, but exercise real state initialization.
    with patch("discord.voice_state.SocketReader") as reader:
        state = client.create_connection_state()
    assert isinstance(state, MeasuredConnectionState)
    assert state.voice_client is client
    reader.return_value.start.assert_called_once()
    assert state.packets_submitted == 0
    assert state.dave_session is None


async def test_wait_for_dave_handshake_then_ready(transport):
    client, state, _ = transport
    state.dave_protocol_version = 1
    state.dave_session = SimpleNamespace(ready=False)
    task = asyncio.create_task(client.wait_for_encryption())
    await asyncio.sleep(0)
    assert not task.done()
    state.dave_session.ready = True
    await task
    assert state.dave_protocol_version == 1
    state.socket.sendall.assert_not_called()


async def test_dave_handshake_timeout_and_cancellation(transport):
    client, state, _ = transport
    state.dave_protocol_version = 1
    state.dave_session = SimpleNamespace(ready=False)
    with pytest.raises(VoiceEncryptionNotReady):
        await client.wait_for_encryption(timeout=0.001)
    task = asyncio.create_task(client.wait_for_encryption())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert state.dave_protocol_version == 1
    state.socket.sendall.assert_not_called()


async def test_protocol_zero_needs_no_dave_session(transport):
    client, _, _ = transport
    await client.wait_for_encryption(timeout=0)
