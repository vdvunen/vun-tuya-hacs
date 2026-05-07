"""Fan platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
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
        VunTuyaFan(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "fan"
    )


class VunTuyaFan(VunTuyaEntity, FanEntity):
    """Vertegenwoordigt een Tuya ventilator."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
    )

    @property
    def is_on(self) -> bool | None:
        val = self._get("state")
        return bool(val) if val is not None else None

    @property
    def percentage(self) -> int | None:
        val = self._get("percentage")
        if val is not None:
            return int(val)
        # Fallback: fan_speed_enum → percentage
        speed = self._get("fan_speed")
        if speed is not None:
            try:
                return min(100, max(0, int(speed) * 17))
            except (TypeError, ValueError):
                pass
        return None

    @property
    def preset_mode(self) -> str | None:
        return self._get("preset_mode")

    @property
    def preset_modes(self) -> list[str] | None:
        ha_config = self._entity_config.get("ha_config") or {}
        modes = ha_config.get("preset_modes")
        if modes:
            return modes
        return ["sleep", "normal", "nature", "smart"]

    async def async_turn_on(
        self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any
    ) -> None:
        commands = [{"code": self._dp_code("state"), "value": True}]
        if percentage is not None and (code := self._dp_code("percentage")):
            commands.append({"code": code, "value": percentage})
        if preset_mode is not None and (code := self._dp_code("preset_mode")):
            commands.append({"code": code, "value": preset_mode})
        await self._send(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send_dp("state", False)

    async def async_set_percentage(self, percentage: int) -> None:
        await self._send_dp("percentage", percentage)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._send_dp("preset_mode", preset_mode)
