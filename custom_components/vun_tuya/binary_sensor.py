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

from .const import BINARY_SENSOR_DPS, CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN
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
    "vibration": BinarySensorDeviceClass.VIBRATION,
    "window": BinarySensorDeviceClass.WINDOW,
    "plug": BinarySensorDeviceClass.PLUG,
    "sound": BinarySensorDeviceClass.SOUND,
    "tamper": BinarySensorDeviceClass.TAMPER,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer binary sensor entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[VunTuyaBinarySensor] = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            status: list[dict] = device.get("status") or []
            codes = {item["code"] for item in status}

            for dp_code, dp_info in BINARY_SENSOR_DPS.items():
                if dp_code in codes:
                    entities.append(
                        VunTuyaBinarySensor(coordinator, device_id, dp_code, dp_info)
                    )

    async_add_entities(entities)


class VunTuyaBinarySensor(VunTuyaEntity, BinarySensorEntity):
    """Vertegenwoordigt een Tuya binaire sensor (beweging, deur, rook, etc.)."""

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
        self._on_value = dp_info.get("on_value", True)
        self._attr_unique_id = f"{device_id}_{dp_code}"
        self._attr_name = dp_info.get("name", dp_code)
        device_class_str = dp_info.get("device_class")
        self._attr_device_class = DEVICE_CLASS_MAP.get(device_class_str) if device_class_str else None

    @property
    def is_on(self) -> bool | None:
        """Geeft True terug als de sensor geactiveerd is."""
        val = self._get_dp_value(self._dp_code)
        if val is None:
            return None
        return val == self._on_value
