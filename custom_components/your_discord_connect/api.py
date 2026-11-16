"""Read-only Discord REST client for server discovery and member identities."""

from dataclasses import dataclass
from time import monotonic

import aiohttp

from .const import API_BASE


class DiscordError(Exception):
    """A Discord request failed, without including credentials or response bodies."""


class DiscordAuthError(DiscordError):
    """The bot token is invalid."""


class DiscordPermissionError(DiscordError):
    """The bot cannot read this server's members."""


class DiscordNotFoundError(DiscordError):
    """The server is no longer accessible."""


class DiscordRateLimitError(DiscordError):
    """Discord rate limited a request; retry on the next scheduled update."""


@dataclass(frozen=True)
class Member:
    """A Discord member, identified independently of their display name."""

    id: str
    display_name: str
    username: str = ""
    presence: str | None = None
    in_voice_channel: bool | None = None
    voice_channel: str | None = None


class DiscordClient:
    """Use Home Assistant's shared session with per-request authentication."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._token = token
        self._retry_at = 0.0

    async def _get(self, path: str, params: dict | None = None):
        if monotonic() < self._retry_at:
            raise DiscordRateLimitError
        try:
            async with self._session.get(
                f"{API_BASE}{path}",
                headers={
                    "Authorization": f"Bot {self._token}",
                    "User-Agent": (
                        "DiscordBot (https://github.com/davidbreitung/your_discord_connect, 0.2.0)"
                    ),
                },
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
                allow_redirects=False,
            ) as response:
                if response.status == 401:
                    raise DiscordAuthError
                if response.status == 403:
                    raise DiscordPermissionError
                if response.status == 404:
                    raise DiscordNotFoundError
                if response.status == 429:
                    try:
                        retry_after = float(response.headers.get("Retry-After", "60"))
                    except ValueError:
                        retry_after = 60
                    self._retry_at = monotonic() + max(1, retry_after)
                    raise DiscordRateLimitError
                if response.status != 200:
                    raise DiscordError(f"Discord returned HTTP {response.status}")
                return await response.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise DiscordError("Cannot read Discord response") from err

    async def guilds(self) -> dict[str, str]:
        """List every server the bot has joined, including pagination."""
        guilds: dict[str, str] = {}
        after = "0"
        while True:
            page = await self._get("/users/@me/guilds", {"limit": 200, "after": after})
            try:
                if not isinstance(page, list):
                    raise ValueError("Expected a server list")
                for guild in page:
                    if not str(guild["id"]).isdigit() or not isinstance(guild["name"], str):
                        raise ValueError("Invalid server")
                    guilds[str(guild["id"])] = guild["name"]
                if len(page) < 200:
                    return guilds
                next_after = str(page[-1]["id"])
                if int(next_after) <= int(after):
                    raise ValueError("Pagination did not advance")
                after = next_after
            except (KeyError, TypeError, ValueError) as err:
                raise DiscordError("Invalid server list") from err

    async def guild_name(self, guild_id: str) -> str:
        guild = await self._get(f"/guilds/{guild_id}")
        try:
            if not isinstance(guild["name"], str):
                raise ValueError("Expected a server name")
            return guild["name"]
        except (KeyError, TypeError, ValueError) as err:
            raise DiscordError("Invalid server response") from err

    async def members(self, guild_id: str) -> dict[str, Member]:
        """Return a complete snapshot; never return partial results after an error."""
        members: dict[str, Member] = {}
        after = "0"
        while True:
            page = await self._get(f"/guilds/{guild_id}/members", {"limit": 1000, "after": after})
            try:
                if not isinstance(page, list):
                    raise ValueError("Expected a member list")
                for item in page:
                    user = item["user"]
                    member_id = str(user["id"])
                    name = item.get("nick") or user.get("global_name") or user["username"]
                    if not member_id.isdigit() or not isinstance(name, str) or not name:
                        raise ValueError("Invalid member")
                    username = user["username"]
                    if not isinstance(username, str) or not username:
                        raise ValueError("Invalid username")
                    members[member_id] = Member(member_id, name, username)
                if len(page) < 1000:
                    return members
                next_after = str(page[-1]["user"]["id"])
                if int(next_after) <= int(after):
                    raise ValueError("Pagination did not advance")
                after = next_after
            except (KeyError, TypeError, ValueError) as err:
                raise DiscordError("Invalid member list") from err
