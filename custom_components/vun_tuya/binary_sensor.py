"""Binary sensor platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

DEVICE_CLASS_MAP: dict[str, BinarySensorDeviceClass] = {
    "motion": BinarySensorDeviceClass.MOTION,
    "door": BinarySensorDeviceClass.DOOR,
    "smoke": BinarySensorDeviceClass.SMOKE,
    "gas": BinarySensorDeviceClass.GAS,
    "moisture": BinarySensorDeviceClass.MOISTURE,
    "lock": BinarySensorDeviceClass.LOCK,
    "heat": BinarySensorDeviceClass.HEAT,
    "sound": BinarySensorDeviceClass.SOUND,
    "vibration": BinarySensorDeviceClass.VIBRATION,
    "window": BinarySensorDeviceClass.WINDOW,
    "occupancy": BinarySensorDeviceClass.OCCUPANCY,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaBinarySensor(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] in ("binary_sensor", "doorbell")
    )


class VunTuyaBinarySensor(VunTuyaEntity, BinarySensorEntity):
    """Vertegenwoordigt een Tuya binaire sensor of videodeurbel."""

    def __init__(self, coordinator: VunTuyaCoordinator, entity_config: dict) -> None:
        super().__init__(coordinator, entity_config)
        ha_config = entity_config.get("ha_config") or {}
        dc = ha_config.get("device_class")
        self._attr_device_class = DEVICE_CLASS_MAP.get(dc) if dc else None

    @property
    def is_on(self) -> bool | None:
        val = self._get("state") or self._get("ring") or self._get("motion")
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "pir", "alarm", "ring", "1")
        return bool(val)
