"""Vacuum platform voor VUN Tuya integratie (robotstofzuigers)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

# Tuya status waarden → HA states
VACUUM_STATE_MAP: dict[str, str] = {
    "standby":      STATE_IDLE,
    "idle":         STATE_IDLE,
    "smart_clean":  STATE_CLEANING,
    "auto_clean":   STATE_CLEANING,
    "zone_clean":   STATE_CLEANING,
    "SelectRoom":   STATE_CLEANING,
    "cleaning":     STATE_CLEANING,
    "goto_point":   STATE_CLEANING,
    "pose_find":    STATE_IDLE,
    "charge_state": STATE_DOCKED,
    "charging":     STATE_DOCKED,
    "fully_charged": STATE_DOCKED,
    "paused":       STATE_PAUSED,
    "pause":        STATE_PAUSED,
    "goto_charge":  STATE_RETURNING,
    "back_charge":  STATE_RETURNING,
    "fault":        STATE_ERROR,
    "error":        STATE_ERROR,
}

VACUUM_CATEGORIES = {"sd", "sweeper", "mop", "sz", "sdmop"}


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
            if CATEGORY_PLATFORM_MAP.get(category) == "vacuum" or category in VACUUM_CATEGORIES:
                entities.append(VunTuyaVacuum(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaVacuum(VunTuyaEntity, StateVacuumEntity):
    """Vertegenwoordigt een Tuya robotstofzuiger."""

    _attr_name = None
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.STATUS
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
    )

    FAN_SPEED_LIST = ["gentle", "normal", "strong", "max"]

    @property
    def state(self) -> str | None:
        val = self._get_dp_value("status")
        if val is None:
            return None
        return VACUUM_STATE_MAP.get(str(val), STATE_IDLE)

    @property
    def battery_level(self) -> int | None:
        val = self._get_dp_value("battery_percentage", "battery")
        if val is None:
            return None
        return int(val)

    @property
    def fan_speed(self) -> str | None:
        return self._get_dp_value("suction")

    @property
    def fan_speed_list(self) -> list[str]:
        return self.FAN_SPEED_LIST

    async def async_start(self) -> None:
        await self._async_send([{"code": "status", "value": "smart_clean"}])

    async def async_stop(self, **kwargs: Any) -> None:
        await self._async_send([{"code": "status", "value": "standby"}])

    async def async_pause(self) -> None:
        if self._has_dp("pause"):
            await self._async_send([{"code": "pause", "value": True}])
        else:
            await self._async_send([{"code": "status", "value": "paused"}])

    async def async_return_to_base(self, **kwargs: Any) -> None:
        if self._has_dp("charge_state"):
            await self._async_send([{"code": "charge_state", "value": True}])
        else:
            await self._async_send([{"code": "status", "value": "goto_charge"}])

    async def async_locate(self, **kwargs: Any) -> None:
        if self._has_dp("seek"):
            await self._async_send([{"code": "seek", "value": True}])

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        await self._async_send([{"code": "suction", "value": fan_speed}])

    def _has_dp(self, code: str) -> bool:
        status: list[dict] = self._device_data.get("status") or []
        return any(item["code"] == code for item in status)
