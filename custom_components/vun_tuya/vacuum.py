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

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

VACUUM_STATE_MAP: dict[str, str] = {
    "standby":       STATE_IDLE,
    "idle":          STATE_IDLE,
    "smart_clean":   STATE_CLEANING,
    "auto_clean":    STATE_CLEANING,
    "zone_clean":    STATE_CLEANING,
    "SelectRoom":    STATE_CLEANING,
    "cleaning":      STATE_CLEANING,
    "goto_point":    STATE_CLEANING,
    "pose_find":     STATE_IDLE,
    "charge_state":  STATE_DOCKED,
    "charging":      STATE_DOCKED,
    "fully_charged": STATE_DOCKED,
    "paused":        STATE_PAUSED,
    "pause":         STATE_PAUSED,
    "goto_charge":   STATE_RETURNING,
    "back_charge":   STATE_RETURNING,
    "fault":         STATE_ERROR,
    "error":         STATE_ERROR,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaVacuum(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "vacuum"
    )


class VunTuyaVacuum(VunTuyaEntity, StateVacuumEntity):
    """Vertegenwoordigt een Tuya robotstofzuiger."""

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
    _attr_fan_speed_list = ["gentle", "normal", "strong", "max"]

    @property
    def state(self) -> str | None:
        val = self._get("status")
        return VACUUM_STATE_MAP.get(str(val), STATE_IDLE) if val is not None else None

    @property
    def battery_level(self) -> int | None:
        val = self._get("battery")
        return int(val) if val is not None else None

    @property
    def fan_speed(self) -> str | None:
        return self._get("fan_speed")

    async def async_start(self) -> None:
        await self._send_dp("status", "smart_clean")

    async def async_stop(self, **kwargs: Any) -> None:
        await self._send_dp("status", "standby")

    async def async_pause(self) -> None:
        if code := self._dp_code("pause"):
            await self._send([{"code": code, "value": True}])
        else:
            await self._send_dp("status", "paused")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self._send_dp("status", "goto_charge")

    async def async_locate(self, **kwargs: Any) -> None:
        if code := self._dp_code("seek"):
            await self._send([{"code": code, "value": True}])

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        await self._send_dp("fan_speed", fan_speed)
