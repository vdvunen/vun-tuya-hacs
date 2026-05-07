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

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

ALARM_STATE_MAP: dict[str, AlarmControlPanelState] = {
    "disarmed":  AlarmControlPanelState.DISARMED,
    "arm":       AlarmControlPanelState.ARMED_AWAY,
    "home":      AlarmControlPanelState.ARMED_HOME,
    "sos":       AlarmControlPanelState.TRIGGERED,
    "alarm":     AlarmControlPanelState.TRIGGERED,
    "triggered": AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaAlarm(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "alarm_control_panel"
    )


class VunTuyaAlarm(VunTuyaEntity, AlarmControlPanelEntity):
    """Vertegenwoordigt een Tuya alarmpaneel."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.TRIGGER
    )
    _attr_code_format = None

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        val = self._get("alarm_state") or self._get("state")
        if val is None:
            return None
        if isinstance(val, bool):
            return AlarmControlPanelState.ARMED_AWAY if val else AlarmControlPanelState.DISARMED
        return ALARM_STATE_MAP.get(str(val), AlarmControlPanelState.DISARMED)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._send_dp("alarm_state", "disarmed")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._send_dp("alarm_state", "home")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._send_dp("alarm_state", "arm")

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        await self._send_dp("alarm_state", "sos")
