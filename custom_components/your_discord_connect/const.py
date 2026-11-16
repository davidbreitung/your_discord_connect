"""Constants for Your Discord Connect."""

DOMAIN = "your_discord_connect"
CONF_GUILD_ID = "guild_id"
CONF_SYNC_INTERVAL = "sync_interval"
DEFAULT_SYNC_INTERVAL = 30
MEMBER_SENSOR_KEYS = (
    "display_name",
    "username",
    "presence",
    "voice_channel",
    "last_present",
    "last_absent",
    "last_gateway_event",
)
MEMBER_BINARY_KEYS = ("in_voice_channel", "speaker_muted", "microphone_muted", "in_afk_channel")
MAX_SYNC_INTERVAL = 1440
API_BASE = "https://discord.com/api/v10"
