"""Cover platform voor VUN Tuya integratie (rolluiken, gordijnen)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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
        VunTuyaCover(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "cover"
    )


class VunTuyaCover(VunTuyaEntity, CoverEntity):
    """Vertegenwoordigt een Tuya rolluik of gordijn."""

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    @property
    def current_cover_position(self) -> int | None:
        val = self._get("current_position") or self._get("position")
        return int(val) if val is not None else None

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        return pos == 0 if pos is not None else None

    async def async_open_cover(self, **kwargs: Any) -> None:
        if code := self._dp_code("state"):
            await self._send([{"code": code, "value": "open"}])

    async def async_close_cover(self, **kwargs: Any) -> None:
        if code := self._dp_code("state"):
            await self._send([{"code": code, "value": "close"}])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        if code := self._dp_code("state"):
            await self._send([{"code": code, "value": "stop"}])

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs.get(ATTR_POSITION, 0)
        await self._send_dp("position", position)
