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
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CATEGORY_PLATFORM_MAP,
    DATA_COORDINATOR,
    DOMAIN,
    LIGHT_DPS,
)
from .coordinator import VunTuyaCoordinator
from .entity import VunTuyaEntity

_LOGGER = logging.getLogger(__name__)

TUYA_MIN_BRIGHTNESS = 10
TUYA_MAX_BRIGHTNESS = 1000
TUYA_MIN_COLOR_TEMP = 0
TUYA_MAX_COLOR_TEMP = 1000
HA_MIN_KELVIN = 2700
HA_MAX_KELVIN = 6500


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialiseer light entities vanuit een config entry."""
    coordinator: VunTuyaCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []
    if coordinator.data:
        for device_id, device in coordinator.data.items():
            category = device.get("category", "")
            if CATEGORY_PLATFORM_MAP.get(category) == "light":
                entities.append(VunTuyaLight(coordinator, device_id))

    async_add_entities(entities)


class VunTuyaLight(VunTuyaEntity, LightEntity):
    """Vertegenwoordigt een Tuya lichtapparaat."""

    _attr_name = None

    def __init__(self, coordinator: VunTuyaCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._determine_color_modes()

    def _determine_color_modes(self) -> None:
        """Stel de ondersteunde kleurmodi in op basis van aanwezige DP codes."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}

        modes: set[ColorMode] = set()

        has_color = any(c in codes for c in LIGHT_DPS["color"])
        has_color_temp = any(c in codes for c in LIGHT_DPS["color_temp"])
        has_brightness = any(c in codes for c in LIGHT_DPS["brightness"])

        if has_color:
            modes.add(ColorMode.HS)
        if has_color_temp:
            modes.add(ColorMode.COLOR_TEMP)
        if has_brightness and not has_color and not has_color_temp:
            modes.add(ColorMode.BRIGHTNESS)
        if not modes:
            modes.add(ColorMode.ONOFF)

        self._attr_supported_color_modes = modes
        if ColorMode.HS in modes:
            self._attr_color_mode = ColorMode.HS
        elif ColorMode.COLOR_TEMP in modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif ColorMode.BRIGHTNESS in modes:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF

        if len(modes) > 1 or ColorMode.HS in modes or ColorMode.COLOR_TEMP in modes:
            self._attr_supported_features = LightEntityFeature(0)

    @property
    def is_on(self) -> bool | None:
        """Geeft True terug als het licht aan is."""
        val = self._get_dp_value(*LIGHT_DPS["switch"])
        if val is None:
            return None
        return bool(val)

    @property
    def brightness(self) -> int | None:
        """Geeft de helderheid terug (0-255)."""
        val = self._get_dp_value(*LIGHT_DPS["brightness"])
        if val is None:
            return None
        val = int(val)
        return round(
            (val - TUYA_MIN_BRIGHTNESS)
            / (TUYA_MAX_BRIGHTNESS - TUYA_MIN_BRIGHTNESS)
            * 254
        )

    @property
    def color_temp_kelvin(self) -> int | None:
        """Geeft de kleurtemperatuur in Kelvin terug."""
        val = self._get_dp_value(*LIGHT_DPS["color_temp"])
        if val is None:
            return None
        val = int(val)
        # Tuya: 0=warm (2700K), 1000=koud (6500K)
        ratio = val / TUYA_MAX_COLOR_TEMP
        return round(HA_MIN_KELVIN + ratio * (HA_MAX_KELVIN - HA_MIN_KELVIN))

    @property
    def min_color_temp_kelvin(self) -> int:
        return HA_MIN_KELVIN

    @property
    def max_color_temp_kelvin(self) -> int:
        return HA_MAX_KELVIN

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Geeft hue/saturation terug."""
        val = self._get_dp_value(*LIGHT_DPS["color"])
        if val is None or not isinstance(val, dict):
            return None
        h = val.get("h", 0)
        s = val.get("s", 0) / 1000 * 100
        return (h, s)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Zet het licht aan, optioneel met helderheid/kleur."""
        commands: list[dict] = []

        switch_code = self._first_present_code(LIGHT_DPS["switch"])
        commands.append({"code": switch_code, "value": True})

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            tuya_brightness = round(
                TUYA_MIN_BRIGHTNESS
                + (brightness / 254) * (TUYA_MAX_BRIGHTNESS - TUYA_MIN_BRIGHTNESS)
            )
            brightness_code = self._first_present_code(LIGHT_DPS["brightness"])
            if brightness_code:
                commands.append({"code": brightness_code, "value": tuya_brightness})
                work_mode_code = self._first_present_code(LIGHT_DPS["work_mode"])
                if work_mode_code:
                    commands.append({"code": work_mode_code, "value": "white"})

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            ratio = (kelvin - HA_MIN_KELVIN) / (HA_MAX_KELVIN - HA_MIN_KELVIN)
            tuya_temp = round(ratio * TUYA_MAX_COLOR_TEMP)
            temp_code = self._first_present_code(LIGHT_DPS["color_temp"])
            if temp_code:
                commands.append({"code": temp_code, "value": tuya_temp})
                work_mode_code = self._first_present_code(LIGHT_DPS["work_mode"])
                if work_mode_code:
                    commands.append({"code": work_mode_code, "value": "white"})

        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]
            color_code = self._first_present_code(LIGHT_DPS["color"])
            if color_code:
                brightness_val = self.brightness or 128
                tuya_brightness = round(
                    TUYA_MIN_BRIGHTNESS
                    + (brightness_val / 254) * (TUYA_MAX_BRIGHTNESS - TUYA_MIN_BRIGHTNESS)
                )
                commands.append({
                    "code": color_code,
                    "value": {
                        "h": round(hue),
                        "s": round(saturation / 100 * 1000),
                        "v": tuya_brightness,
                    },
                })
                work_mode_code = self._first_present_code(LIGHT_DPS["work_mode"])
                if work_mode_code:
                    commands.append({"code": work_mode_code, "value": "colour"})

        await self._async_send(commands)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Zet het licht uit."""
        switch_code = self._first_present_code(LIGHT_DPS["switch"])
        await self._async_send([{"code": switch_code, "value": False}])

    def _first_present_code(self, candidates: list[str]) -> str:
        """Geeft de eerste DP code terug die aanwezig is in de status."""
        status: list[dict] = self._device_data.get("status") or []
        codes = {item["code"] for item in status}
        for code in candidates:
            if code in codes:
                return code
        return candidates[0]
