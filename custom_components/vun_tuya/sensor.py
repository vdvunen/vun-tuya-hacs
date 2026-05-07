"""Sensor platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

UNIT_MAP: dict[str, str] = {
    "W": UnitOfPower.WATT,
    "mA": UnitOfElectricCurrent.MILLIAMPERE,
    "V": UnitOfElectricPotential.VOLT,
    "°C": UnitOfTemperature.CELSIUS,
    "%": PERCENTAGE,
    "ppm": "ppm",
    "µg/m³": "µg/m³",
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "lx": "lx",
    "min": "min",
    "m²": "m²",
}

DEVICE_CLASS_MAP: dict[str, SensorDeviceClass] = {
    "power": SensorDeviceClass.POWER,
    "current": SensorDeviceClass.CURRENT,
    "voltage": SensorDeviceClass.VOLTAGE,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "humidity": SensorDeviceClass.HUMIDITY,
    "battery": SensorDeviceClass.BATTERY,
    "carbon_dioxide": SensorDeviceClass.CO2,
    "pm25": SensorDeviceClass.PM25,
    "energy": SensorDeviceClass.ENERGY,
    "illuminance": SensorDeviceClass.ILLUMINANCE,
}

STATE_CLASS_MAP: dict[str, SensorStateClass] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
    "total": SensorStateClass.TOTAL,
}

# Schaalfactoren voor bekende DP codes
SCALE_MAP: dict[str, float] = {
    "cur_power": 0.1,
    "cur_voltage": 0.1,
    "va_temperature": 0.1,
    "temp_current": 0.1,
    "energy_today": 0.01,
    "energy_total": 0.01,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaSensor(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "sensor"
    )


class VunTuyaSensor(VunTuyaEntity, SensorEntity):
    """Vertegenwoordigt een Tuya sensor."""

    def __init__(self, coordinator: VunTuyaCoordinator, entity_config: dict) -> None:
        super().__init__(coordinator, entity_config)
        ha_config = entity_config.get("ha_config") or {}

        unit_str = ha_config.get("unit_of_measurement", "")
        self._attr_native_unit_of_measurement = UNIT_MAP.get(unit_str, unit_str or None)

        dc = ha_config.get("device_class")
        self._attr_device_class = DEVICE_CLASS_MAP.get(dc) if dc else None

        sc = ha_config.get("state_class", "measurement")
        self._attr_state_class = STATE_CLASS_MAP.get(sc, SensorStateClass.MEASUREMENT)

        # Bepaal schaalfactor op basis van gemapte DP code
        state_dp = self._attr_map.get("state", "")
        self._scale = SCALE_MAP.get(state_dp, 1.0)

    @property
    def native_value(self) -> float | str | None:
        val = self._get("state")
        if val is None:
            return None
        try:
            numeric = float(val) * self._scale
            return round(numeric, 2) if numeric != int(numeric) else int(numeric)
        except (TypeError, ValueError):
            return str(val)
