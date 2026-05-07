"""Climate platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

TUYA_TO_HA_HVAC: dict[str, HVACMode] = {
    "auto": HVACMode.AUTO,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
    "fan": HVACMode.FAN_ONLY,
    "wind": HVACMode.FAN_ONLY,
    "dry":  HVACMode.DRY,
    "off":  HVACMode.OFF,
}
HA_TO_TUYA_HVAC: dict[HVACMode, str] = {v: k for k, v in TUYA_TO_HA_HVAC.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaClimate(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "climate"
    )


class VunTuyaClimate(VunTuyaEntity, ClimateEntity):
    """Vertegenwoordigt een Tuya klimaatapparaat."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.FAN_ONLY]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )

    @property
    def hvac_mode(self) -> HVACMode | None:
        # Controleer eerst de switch
        on_val = self._get("state")
        if on_val is False:
            return HVACMode.OFF
        mode_val = self._get("hvac_mode")
        if mode_val:
            return TUYA_TO_HA_HVAC.get(str(mode_val), HVACMode.HEAT)
        if on_val is True:
            return HVACMode.HEAT
        return None

    @property
    def current_temperature(self) -> float | None:
        val = self._get("current_temperature")
        if val is None:
            return None
        raw = float(val)
        # Tuya stuurt vaak temperatuur * 10 (bijv. 215 = 21.5°C)
        return raw / 10 if raw > 100 else raw

    @property
    def target_temperature(self) -> float | None:
        val = self._get("target_temperature")
        if val is None:
            return None
        raw = float(val)
        return raw / 10 if raw > 100 else raw

    @property
    def min_temp(self) -> float:
        return float(self._entity_config.get("ha_config", {}).get("min_temp", 5))

    @property
    def max_temp(self) -> float:
        return float(self._entity_config.get("ha_config", {}).get("max_temp", 35))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._send_dp("state", False)
        else:
            commands: list[dict] = []
            if code := self._dp_code("state"):
                commands.append({"code": code, "value": True})
            tuya_mode = HA_TO_TUYA_HVAC.get(hvac_mode)
            if tuya_mode and (code := self._dp_code("hvac_mode")):
                commands.append({"code": code, "value": tuya_mode})
            await self._send(commands)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        val = self._get("target_temperature")
        tuya_val = round(temp * 10) if (val is not None and float(val) > 100) else round(temp)
        await self._send_dp("target_temperature", tuya_val)

    async def async_turn_on(self) -> None:
        await self._send_dp("state", True)

    async def async_turn_off(self) -> None:
        await self._send_dp("state", False)
