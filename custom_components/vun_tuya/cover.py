"""Cover platform voor VUN Tuya integratie (rolluiken, gordijnen, garagedeuren)."""
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

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

COVER_CATEGORIES = {"cl", "clkg", "cz_cl", "wkcz"}

COVER_DPS = {
    "control": ["control", "mach_operate", "work_state"],
    "position": ["percent_control", "position"],
    "current_position": ["percent_state", "position_state"],
}


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
            if CATEGORY_PLATFORM_MAP.get(category) == "cover" or category in COVER_CATEGORIES:
                entities.append(VunTuyaCover(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaCover(VunTuyaEntity, CoverEntity):
    """Vertegenwoordigt een Tuya rolluik of gordijn."""

    _attr_name = None
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    @property
    def current_cover_position(self) -> int | None:
        val = self._get_dp_value(*COVER_DPS["current_position"])
        if val is None:
            val = self._get_dp_value(*COVER_DPS["position"])
        if val is None:
            return None
        return int(val)

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    @property
    def is_opening(self) -> bool:
        state = self._get_dp_value(*COVER_DPS["control"])
        return state == "open"

    @property
    def is_closing(self) -> bool:
        state = self._get_dp_value(*COVER_DPS["control"])
        return state == "close"

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._async_send([{"code": "control", "value": "open"}])

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._async_send([{"code": "control", "value": "close"}])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._async_send([{"code": "control", "value": "stop"}])

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs.get(ATTR_POSITION, 0)
        control_code = self._first_present_code(COVER_DPS["position"])
        await self._async_send([{"code": control_code, "value": position}])

    def _first_present_code(self, candidates: list[str]) -> str:
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}
        for code in candidates:
            if code in codes:
                return code
        return candidates[0]
