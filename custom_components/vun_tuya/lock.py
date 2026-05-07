"""Lock platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaLock(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "lock"
    )


class VunTuyaLock(VunTuyaEntity, LockEntity):
    """Vertegenwoordigt een Tuya slim slot."""

    @property
    def is_locked(self) -> bool | None:
        val = self._get("locked")
        if val is None:
            val = self._get("state")
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("true", "locked", "closed", "lock")

    async def async_lock(self, **kwargs: Any) -> None:
        if code := self._dp_code("locked"):
            await self._send([{"code": code, "value": True}])
        else:
            await self._send_dp("state", True)

    async def async_unlock(self, **kwargs: Any) -> None:
        if code := self._dp_code("locked"):
            await self._send([{"code": code, "value": False}])
        else:
            await self._send_dp("state", False)
