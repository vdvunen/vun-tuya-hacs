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

from .const import CATEGORY_PLATFORM_MAP, CLIMATE_DPS, DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

TUYA_HVAC_MODE_MAP: dict[str, HVACMode] = {
    "auto": HVACMode.AUTO,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
    "fan": HVACMode.FAN_ONLY,
    "dry": HVACMode.DRY,
    "wind": HVACMode.FAN_ONLY,
}

HA_TO_TUYA_MODE: dict[HVACMode, str] = {v: k for k, v in TUYA_HVAC_MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer climate entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "climate":
                entities.append(VunTuyaClimate(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaClimate(VunTuyaEntity, ClimateEntity):
    """Vertegenwoordigt een Tuya klimaatapparaat (thermostaat, airco, verwarming)."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: VunTuyaCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._determine_features()

    def _determine_features(self) -> None:
        """Stel ondersteunde functies in op basis van aanwezige DP codes."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}

        features = ClimateEntityFeature(0)
        has_target_temp = any(c in codes for c in CLIMATE_DPS["target_temp"])
        has_mode = any(c in codes for c in CLIMATE_DPS["mode"])
        has_fan = any(c in codes for c in CLIMATE_DPS["fan_speed"])
        has_humidity = any(c in codes for c in CLIMATE_DPS["humidity"])

        if has_target_temp:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if has_fan:
            features |= ClimateEntityFeature.FAN_MODE
        if has_humidity:
            features |= ClimateEntityFeature.TARGET_HUMIDITY

        self._attr_supported_features = features

        # HVAC modes op basis van beschikbare mode-waarden
        if has_mode:
            self._attr_hvac_modes = [HVACMode.OFF] + list(TUYA_HVAC_MODE_MAP.values())
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Geeft de huidige HVAC modus terug."""
        switch_val = self._get_dp_value(*CLIMATE_DPS["switch"])
        if switch_val is False or switch_val == 0:
            return HVACMode.OFF

        mode_val = self._get_dp_value(*CLIMATE_DPS["mode"])
        if mode_val:
            return TUYA_HVAC_MODE_MAP.get(str(mode_val).lower(), HVACMode.HEAT)

        # Geen expliciete mode DP — als switch aan is, gebruik HEAT
        if switch_val:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def target_temperature(self) -> float | None:
        """Geeft de doeltemperatuur terug."""
        val = self._get_dp_value(*CLIMATE_DPS["target_temp"])
        if val is None:
            return None
        return _normalize_temp(val)

    @property
    def current_temperature(self) -> float | None:
        """Geeft de huidige temperatuur terug."""
        val = self._get_dp_value(*CLIMATE_DPS["current_temp"])
        if val is None:
            return None
        return _normalize_temp(val)

    @property
    def current_humidity(self) -> int | None:
        """Geeft de huidige luchtvochtigheid terug."""
        val = self._get_dp_value(*CLIMATE_DPS["humidity"])
        if val is None:
            return None
        return int(val)

    @property
    def fan_mode(self) -> str | None:
        """Geeft de ventilatorstand terug."""
        return self._get_dp_value(*CLIMATE_DPS["fan_speed"])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Stel de HVAC modus in."""
        commands: list[dict] = []
        switch_code = self._first_present_code(CLIMATE_DPS["switch"])

        if hvac_mode == HVACMode.OFF:
            commands.append({"code": switch_code, "value": False})
        else:
            commands.append({"code": switch_code, "value": True})
            mode_code = self._first_present_code(CLIMATE_DPS["mode"])
            if mode_code:
                tuya_mode = HA_TO_TUYA_MODE.get(hvac_mode, "auto")
                commands.append({"code": mode_code, "value": tuya_mode})

        await self._async_send(commands)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Stel de doeltemperatuur in."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        temp_code = self._first_present_code(CLIMATE_DPS["target_temp"])
        # Tuya gebruikt integer °C × 10 (bijv. 20.5 → 205) of gewoon integer
        val = self._get_dp_value(*CLIMATE_DPS["target_temp"])
        if isinstance(val, int) and val > 100:
            tuya_temp = round(temp * 10)
        else:
            tuya_temp = round(temp)

        commands = [{"code": temp_code, "value": tuya_temp}]

        if ATTR_HVAC_MODE in kwargs:
            await self.async_set_hvac_mode(kwargs[ATTR_HVAC_MODE])

        await self._async_send(commands)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Stel de ventilatorstand in."""
        fan_code = self._first_present_code(CLIMATE_DPS["fan_speed"])
        await self._async_send([{"code": fan_code, "value": fan_mode}])

    def _first_present_code(self, candidates: list[str]) -> str:
        """Geeft de eerste DP code terug die aanwezig is in de status."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}
        for code in candidates:
            if code in codes:
                return code
        return candidates[0]


def _normalize_temp(val: Any) -> float:
    """Zet Tuya temperatuurwaarden om naar °C (hoog getal = ×0.1)."""
    try:
        v = float(val)
        if v > 100:
            return round(v * 0.1, 1)
        return round(v, 1)
    except (TypeError, ValueError):
        return 0.0
