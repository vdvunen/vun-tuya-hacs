"""Switch platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CATEGORY_PLATFORM_MAP, DATA_COORDINATOR, DOMAIN, SWITCH_DPS
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer switch entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "switch":
                status: list[dict] = device.get("status") or []
                codes = {item["code"] for item in status}

                # Maak een entity per schakelaar DP code
                found = False
                for dp_code in SWITCH_DPS:
                    if dp_code in codes:
                        entities.append(VunTuyaSwitch(coordinator, device_id, dp_code))
                        found = True

                # Fallback: 1 enkele switch entity zonder specifieke DP code
                if not found:
                    entities.append(VunTuyaSwitch(coordinator, device_id, "switch"))

    async_add_entities(entities)


class VunTuyaSwitch(VunTuyaEntity, SwitchEntity):
    """Vertegenwoordigt een Tuya schakelaar (enkele of meervoudige gang)."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(
        self,
        coordinator: VunTuyaCoordinator,
        device_id: str,
        dp_code: str,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._dp_code = dp_code
        # Maak de unique_id uniek per DP code zodat meervoudige schakelaars werken
        self._attr_unique_id = f"{device_id}_{dp_code}"

        # Naam: voor switch_1/switch_2/... voeg een nummer toe
        if dp_code == "switch":
            self._attr_name = None
        elif dp_code.startswith("switch_usb"):
            self._attr_name = f"USB {dp_code.replace('switch_usb', '')}"
        elif "_" in dp_code:
            num = dp_code.rsplit("_", 1)[-1]
            self._attr_name = f"Schakelaar {num}"
        else:
            self._attr_name = None

    @property
    def is_on(self) -> bool | None:
        """Geeft True terug als de schakelaar aan is."""
        val = self._get_dp_value(self._dp_code)
        if val is None:
            return None
        return bool(val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Zet de schakelaar aan."""
        await self._async_send([{"code": self._dp_code, "value": True}])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Zet de schakelaar uit."""
        await self._async_send([{"code": self._dp_code, "value": False}])
