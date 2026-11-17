"""Measure voice transport and prevent sends before negotiated DAVE is ready."""

import asyncio

import discord
from discord.voice_state import VoiceConnectionState


class VoiceEncryptionNotReady(discord.ClientException):
    """Negotiated DAVE has no usable encryption session."""


class MeasuredConnectionState(VoiceConnectionState):
    """Count socket submissions, including OSErrors swallowed by VoiceClient."""

    def __init__(self, voice_client):
        self.reset_diagnostics()
        super().__init__(voice_client)

    def reset_diagnostics(self):
        self.packets_submitted = 0
        self.send_errors = 0
        self.dave_unready_packets = 0
        self.last_dave_protocol = None

    def send_packet(self, packet):
        # No addresses, packet bytes, session identifiers or keys are retained.
        self.last_dave_protocol = self.dave_protocol_version
        if self.dave_protocol_version > 0 and not self.can_encrypt:
            self.dave_unready_packets += 1
            # discord.py otherwise falls back to transport-only encryption.
            # Raise outside its swallowed OSError path so playback reports failure.
            raise VoiceEncryptionNotReady("DAVE session is not ready")
        try:
            super().send_packet(packet)
        except OSError:
            self.send_errors += 1
            raise  # Keep discord.py's existing per-packet error handling.
        else:
            self.packets_submitted += 1

    def diagnostics(self):
        return {
            "last_voice_packets_submitted": self.packets_submitted,
            "last_voice_send_errors": self.send_errors,
            "last_dave_unready_packets": self.dave_unready_packets,
            "last_dave_protocol": self.last_dave_protocol,
        }


class MeasuredVoiceClient(discord.VoiceClient):
    """Use the library's connection-state factory with a DAVE readiness guard.

    VoiceConnectionState is a discord.py implementation detail. Keep its small
    adapter tested against the pinned dependency when upgrading discord.py.
    """

    def create_connection_state(self):
        return MeasuredConnectionState(self)

    def reset_diagnostics(self):
        self._connection.reset_diagnostics()

    def diagnostics(self):
        return self._connection.diagnostics()

    async def wait_for_encryption(self, timeout=10):
        """Allow the initial MLS handshake to finish, without downgrading DAVE."""
        try:
            async with asyncio.timeout(timeout):
                while (
                    self._connection.dave_protocol_version > 0 and not self._connection.can_encrypt
                ):
                    await asyncio.sleep(0.1)
        except TimeoutError as err:
            raise VoiceEncryptionNotReady("DAVE session did not become ready") from err
