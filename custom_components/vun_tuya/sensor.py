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

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN, SENSOR_DPS
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

# Eenheden uit const.py string → HA constante
UNIT_MAP: dict[str, str] = {
    "W": UnitOfPower.WATT,
    "mA": UnitOfElectricCurrent.MILLIAMPERE,
    "V": UnitOfElectricPotential.VOLT,
    "°C": UnitOfTemperature.CELSIUS,
    "%": PERCENTAGE,
    "ppm": "ppm",
    "µg/m³": "µg/m³",
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
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
}

STATE_CLASS_MAP: dict[str, SensorStateClass] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
    "total": SensorStateClass.TOTAL,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer sensor entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[VunTuyaSensor] = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            status: list[dict] = device.get("status") or []
            codes = {item["code"] for item in status}

            # Maak een sensor entity voor elke bekende sensor DP code
            for dp_code, dp_info in SENSOR_DPS.items():
                if dp_code in codes:
                    entities.append(VunTuyaSensor(coordinator, device_id, dp_code, dp_info))

            # Extra sensor entities voor switch-categorie devices met vermogen
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "switch":
                for dp_code, dp_info in SENSOR_DPS.items():
                    if dp_code in codes and dp_code not in {e._dp_code for e in entities}:
                        entities.append(VunTuyaSensor(coordinator, device_id, dp_code, dp_info))

    async_add_entities(entities)


class VunTuyaSensor(VunTuyaEntity, SensorEntity):
    """Vertegenwoordigt een Tuya sensor (vermogen, temperatuur, CO2, etc.)."""

    def __init__(
        self,
        coordinator: VunTuyaCoordinator,
        device_id: str,
        dp_code: str,
        dp_info: dict,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._dp_code = dp_code
        self._dp_info = dp_info
        self._attr_unique_id = f"{device_id}_{dp_code}"
        self._attr_name = dp_info.get("name", dp_code)
        self._attr_native_unit_of_measurement = UNIT_MAP.get(
            dp_info.get("unit", ""), dp_info.get("unit")
        )
        device_class_str = dp_info.get("device_class")
        self._attr_device_class = DEVICE_CLASS_MAP.get(device_class_str) if device_class_str else None
        state_class_str = dp_info.get("state_class")
        self._attr_state_class = STATE_CLASS_MAP.get(state_class_str) if state_class_str else None
        self._scale: float = dp_info.get("scale", 1)

    @property
    def native_value(self) -> float | str | None:
        """Geeft de sensor waarde terug, geschaald indien nodig."""
        val = self._get_dp_value(self._dp_code)
        if val is None:
            return None
        try:
            numeric = float(val)
            scaled = numeric * self._scale
            # Afronden op maximaal 2 decimalen voor leesbaarheid
            return round(scaled, 2) if scaled != int(scaled) else int(scaled)
        except (TypeError, ValueError):
            return str(val)
