"""Fan platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN, FAN_DPS
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_SPEED_LEVELS = ["1", "2", "3", "4", "5", "6"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer fan entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "fan":
                entities.append(VunTuyaFan(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaFan(VunTuyaEntity, FanEntity):
    """Vertegenwoordigt een Tuya ventilator."""

    _attr_name = None

    def __init__(self, coordinator: VunTuyaCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._speed_levels: list[str] = self._detect_speed_levels()
        self._determine_features()

    def _detect_speed_levels(self) -> list[str]:
        """Detecteer de beschikbare snelheidsniveaus vanuit de status."""
        # Probeer de fan_speed_enum waarde te detecteren
        # In de praktijk zijn dit "1"/"2"/"3" of "low"/"mid"/"high"
        return DEFAULT_SPEED_LEVELS

    def _determine_features(self) -> None:
        """Stel ondersteunde functies in op basis van aanwezige DP codes."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}

        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        has_speed_enum = any(c in codes for c in FAN_DPS["speed_enum"])
        has_speed_percent = any(c in codes for c in FAN_DPS["speed_percent"])
        has_oscillate = any(c in codes for c in FAN_DPS["oscillate"])

        if has_speed_enum or has_speed_percent:
            features |= FanEntityFeature.SET_SPEED
        if has_oscillate:
            features |= FanEntityFeature.OSCILLATE

        self._attr_supported_features = features

    @property
    def is_on(self) -> bool | None:
        """Geeft True terug als de ventilator aan is."""
        val = self._get_dp_value(*FAN_DPS["switch"])
        if val is None:
            return None
        return bool(val)

    @property
    def percentage(self) -> int | None:
        """Geeft de snelheid terug als percentage (0-100)."""
        # Probeer eerst percentage DP
        pct = self._get_dp_value(*FAN_DPS["speed_percent"])
        if pct is not None:
            return int(pct)

        # Probeer enum DP
        level = self._get_dp_value(*FAN_DPS["speed_enum"])
        if level is not None and self._speed_levels:
            level_str = str(level)
            if level_str in self._speed_levels:
                return ordered_list_item_to_percentage(self._speed_levels, level_str)
        return None

    @property
    def speed_count(self) -> int:
        return len(self._speed_levels)

    @property
    def oscillating(self) -> bool | None:
        """Geeft True terug als de ventilator oscilleert."""
        val = self._get_dp_value(*FAN_DPS["oscillate"])
        if val is None:
            return None
        return bool(val)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Zet de ventilator aan."""
        commands: list[dict] = []
        switch_code = self._first_present_code(FAN_DPS["switch"])
        commands.append({"code": switch_code, "value": True})

        if percentage is not None:
            speed_cmd = self._build_speed_command(percentage)
            if speed_cmd:
                commands.append(speed_cmd)

        await self._async_send(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Zet de ventilator uit."""
        switch_code = self._first_present_code(FAN_DPS["switch"])
        await self._async_send([{"code": switch_code, "value": False}])

    async def async_set_percentage(self, percentage: int) -> None:
        """Stel de ventilatorsnelheid in als percentage."""
        commands: list[dict] = []
        speed_cmd = self._build_speed_command(percentage)
        if speed_cmd:
            commands.append(speed_cmd)
        if commands:
            await self._async_send(commands)

    async def async_oscillate(self, oscillating: bool) -> None:
        """Schakel oscilleren in of uit."""
        osc_code = self._first_present_code(FAN_DPS["oscillate"])
        await self._async_send([{"code": osc_code, "value": oscillating}])

    def _build_speed_command(self, percentage: int) -> dict | None:
        """Bouw het snelheidscommando op op basis van beschikbare DP codes."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}

        # Percentage DP heeft prioriteit
        for code in FAN_DPS["speed_percent"]:
            if code in codes:
                return {"code": code, "value": percentage}

        # Enum DP
        for code in FAN_DPS["speed_enum"]:
            if code in codes and self._speed_levels:
                level = percentage_to_ordered_list_item(self._speed_levels, percentage)
                return {"code": code, "value": level}

        return None

    def _first_present_code(self, candidates: list[str]) -> str:
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}
        for code in candidates:
            if code in codes:
                return code
        return candidates[0]
