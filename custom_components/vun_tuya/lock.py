"""Lock platform voor VUN Tuya integratie (smart locks, deursloten)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

LOCK_CATEGORIES = {"ms", "jtmspro", "videolock", "dghsfmzq"}

LOCK_DPS_STATE = ["closed", "lock_state", "alarm_lock", "switch"]
LOCK_DPS_OPEN  = ["open"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "lock" or category in LOCK_CATEGORIES:
                entities.append(VunTuyaLock(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaLock(VunTuyaEntity, LockEntity):
    """Vertegenwoordigt een Tuya slim slot."""

    _attr_name = None

    @property
    def is_locked(self) -> bool | None:
        for code in LOCK_DPS_STATE:
            val = self._get_dp_value(code)
            if val is not None:
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ("locked", "true", "lock", "closed", "close")
        return None

    @property
    def is_locking(self) -> bool:
        return False

    @property
    def is_unlocking(self) -> bool:
        return False

    async def async_lock(self, **kwargs: Any) -> None:
        await self._async_send([{"code": "closed", "value": True}])

    async def async_unlock(self, **kwargs: Any) -> None:
        # Sommige Tuya sloten gebruiken een apart 'open' DP om te ontgrendelen
        if self._has_dp("open"):
            await self._async_send([{"code": "open", "value": True}])
        else:
            await self._async_send([{"code": "closed", "value": False}])

    def _has_dp(self, code: str) -> bool:
        status: list[dict] = self._device_data.get("status") or []
        return any(item["code"] == code for item in status)
