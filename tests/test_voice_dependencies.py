"""Exercise the native crypto API used by discord.py with HA's PyNaCl."""

from types import SimpleNamespace

import discord
import nacl.secret
import pytest


def test_discord_voice_packet_encryption():
    key = bytes(range(32))
    client = SimpleNamespace(secret_key=key, _incr_nonce=0)

    def checked_add(attribute, value, limit):
        discord.VoiceClient.checked_add(client, attribute, value, limit)

    client.checked_add = checked_add
    header = bytes(range(12))
    payload = b"opus audio packet"
    packets = []
    for _ in range(2):
        packet = discord.VoiceClient._encrypt_aead_xchacha20_poly1305_rtpsize(
            client, header, payload
        )
        assert packet[:12] == header
        nonce = packet[-4:] + bytes(20)
        assert nacl.secret.Aead(key).decrypt(packet[12:-4], header, nonce) == payload
        with pytest.raises(nacl.exceptions.CryptoError):
            nacl.secret.Aead(key).decrypt(packet[12:-4], bytes(12), nonce)
        packets.append(packet)
    assert packets[0] != packets[1]
    assert client._incr_nonce == 2
