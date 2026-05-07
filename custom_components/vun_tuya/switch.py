"""Switch platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        VunTuyaSwitch(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "switch"
    )


class VunTuyaSwitch(VunTuyaEntity, SwitchEntity):
    """Vertegenwoordigt een Tuya schakelaar."""

    @property
    def is_on(self) -> bool | None:
        val = self._get("state")
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._send_dp("state", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send_dp("state", False)
