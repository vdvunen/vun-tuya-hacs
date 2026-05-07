"""Alarm control panel platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

ALARM_CATEGORIES = {"alarm", "wg", "mal"}

# Tuya master_state waarden → HA AlarmControlPanelState
ALARM_STATE_MAP: dict[str, AlarmControlPanelState] = {
    "disarmed":  AlarmControlPanelState.DISARMED,
    "arm":       AlarmControlPanelState.ARMED_AWAY,
    "home":      AlarmControlPanelState.ARMED_HOME,
    "sos":       AlarmControlPanelState.TRIGGERED,
    "alarm":     AlarmControlPanelState.TRIGGERED,
    "triggered": AlarmControlPanelState.TRIGGERED,
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
            if (
                CATEGORY_PLATFORM_MAP.get(category) == "alarm_control_panel"
                or category in ALARM_CATEGORIES
            ):
                entities.append(VunTuyaAlarm(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaAlarm(VunTuyaEntity, AlarmControlPanelEntity):
    """Vertegenwoordigt een Tuya alarmpaneel."""

    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.TRIGGER
    )
    _attr_code_format = None

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        val = self._get_dp_value("master_state", "alarm_switch")
        if val is None:
            return None
        if isinstance(val, bool):
            return AlarmControlPanelState.ARMED_AWAY if val else AlarmControlPanelState.DISARMED
        return ALARM_STATE_MAP.get(str(val), AlarmControlPanelState.DISARMED)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._send_state("disarmed")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._send_state("home")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._send_state("arm")

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        await self._send_state("sos")

    async def _send_state(self, value: str) -> None:
        dp = "master_state" if self._has_dp("master_state") else "alarm_switch"
        if dp == "alarm_switch":
            payload = value not in ("disarmed", False)
        else:
            payload = value
        await self._async_send([{"code": dp, "value": payload}])

    def _has_dp(self, code: str) -> bool:
        status: list[dict] = self._device_data.get("status") or []
        return any(item["code"] == code for item in status)
