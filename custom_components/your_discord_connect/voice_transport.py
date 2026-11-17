"""Observe discord.py's actual send path without changing encryption or retry policy."""

import discord
from discord.voice_state import VoiceConnectionState


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
    """Use the library's connection-state factory and unchanged audio implementation.

    VoiceConnectionState is a discord.py implementation detail. Keep its small
    adapter tested against the pinned dependency when upgrading discord.py.
    """

    def create_connection_state(self):
        return MeasuredConnectionState(self)

    def reset_diagnostics(self):
        self._connection.reset_diagnostics()

    def diagnostics(self):
        return self._connection.diagnostics()
