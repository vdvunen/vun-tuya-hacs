"""Light platform voor VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

TUYA_MIN_BRIGHTNESS = 10
TUYA_MAX_BRIGHTNESS = 1000
HA_MIN_KELVIN = 2700
HA_MAX_KELVIN = 6500


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(
        VunTuyaLight(coordinator, e)
        for e in coordinator.entities_config
        if e["entity_type"] == "light"
    )


class VunTuyaLight(VunTuyaEntity, LightEntity):
    """Vertegenwoordigt een Tuya lamp."""

    def __init__(self, coordinator: VunTuyaCoordinator, entity_config: dict) -> None:
        super().__init__(coordinator, entity_config)
        modes: set[ColorMode] = set()
        if "rgb_color" in self._attr_map:
            modes.add(ColorMode.HS)
        if "color_temp" in self._attr_map:
            modes.add(ColorMode.COLOR_TEMP)
        if "brightness" in self._attr_map and not modes:
            modes.add(ColorMode.BRIGHTNESS)
        if not modes:
            modes.add(ColorMode.ONOFF)
        self._attr_supported_color_modes = modes
        self._attr_color_mode = next(iter(
            [ColorMode.HS, ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS, ColorMode.ONOFF]
            for m in [[ColorMode.HS, ColorMode.COLOR_TEMP, ColorMode.BRIGHTNESS, ColorMode.ONOFF]
                      if cm in modes else [] for cm in modes]
        ), ColorMode.ONOFF)
        # Eenvoudigere color_mode selectie
        if ColorMode.HS in modes:
            self._attr_color_mode = ColorMode.HS
        elif ColorMode.COLOR_TEMP in modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif ColorMode.BRIGHTNESS in modes:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool | None:
        val = self._get("state")
        return bool(val) if val is not None else None

    @property
    def brightness(self) -> int | None:
        val = self._get("brightness")
        if val is None:
            return None
        raw = int(val)
        # Tuya 10-1000 → HA 0-255
        return round((raw - TUYA_MIN_BRIGHTNESS) / (TUYA_MAX_BRIGHTNESS - TUYA_MIN_BRIGHTNESS) * 254)

    @property
    def color_temp_kelvin(self) -> int | None:
        val = self._get("color_temp")
        if val is None:
            return None
        ratio = int(val) / 1000
        return round(HA_MIN_KELVIN + ratio * (HA_MAX_KELVIN - HA_MIN_KELVIN))

    @property
    def min_color_temp_kelvin(self) -> int:
        return HA_MIN_KELVIN

    @property
    def max_color_temp_kelvin(self) -> int:
        return HA_MAX_KELVIN

    @property
    def hs_color(self) -> tuple[float, float] | None:
        val = self._get("rgb_color")
        if not isinstance(val, dict):
            return None
        return (val.get("h", 0), val.get("s", 0) / 1000 * 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        commands = [{"code": self._dp_code("state"), "value": True}]

        if ATTR_BRIGHTNESS in kwargs:
            raw = round(
                TUYA_MIN_BRIGHTNESS
                + (kwargs[ATTR_BRIGHTNESS] / 254) * (TUYA_MAX_BRIGHTNESS - TUYA_MIN_BRIGHTNESS)
            )
            if code := self._dp_code("brightness"):
                commands.append({"code": code, "value": raw})

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            ratio = (kwargs[ATTR_COLOR_TEMP_KELVIN] - HA_MIN_KELVIN) / (HA_MAX_KELVIN - HA_MIN_KELVIN)
            if code := self._dp_code("color_temp"):
                commands.append({"code": code, "value": round(ratio * 1000)})

        if ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            if code := self._dp_code("rgb_color"):
                commands.append({"code": code, "value": {"h": round(hue), "s": round(sat / 100 * 1000), "v": 1000}})

        await self._send(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send_dp("state", False)
