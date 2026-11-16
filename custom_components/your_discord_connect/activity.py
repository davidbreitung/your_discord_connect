"""Persist observation timestamps without treating a connection loss as absence."""

from dataclasses import replace

from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN


class ActivityTracker:
    def __init__(self, hass, guild_id):
        self.store = Store(hass, 1, f"{DOMAIN}.{guild_id}.activity")
        self.records = {}
        self.loaded = False

    async def load(self):
        if not self.loaded:
            self.records = await self.store.async_load() or {}
            self.loaded = True

    def observe(self, member):
        record = self.records.setdefault(member.id, {})
        now = member.last_gateway_event or dt_util.utcnow()
        if member.last_gateway_event:
            record["last_gateway_event"] = member.last_gateway_event.isoformat()
        present = None
        if member.presence in ("online", "idle", "dnd") or member.in_voice_channel is True:
            present = True
        elif member.presence == "offline" and member.in_voice_channel is False:
            present = False
        if present is not None and record.get("present") != present:
            record["last_present" if present else "last_absent"] = now.isoformat()
            record["present"] = present
        return replace(
            member,
            **{
                key: dt_util.parse_datetime(record[key]) if record.get(key) else None
                for key in ("last_present", "last_absent", "last_gateway_event")
            },
        )

    def schedule_save(self):
        self.store.async_delay_save(lambda: self.records, 5)

    async def close(self):
        if self.loaded:
            await self.store.async_save(self.records)
