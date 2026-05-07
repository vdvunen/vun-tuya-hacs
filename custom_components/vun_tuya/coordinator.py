"""DataUpdateCoordinator voor VUN Tuya — verbindt met de VUN-Tuya-Hassio API."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class VunTuyaCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """
    Centrale data-coordinator voor alle VUN Tuya entities.

    data structuur na update:
    {
        "<device_id>": {"switch_led": True, "bright_value_v2": 500, ...},
        ...
    }

    entities: lijst van alle entity configs opgehaald via de discovery API.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.host: str = entry.data[CONF_HOST].rstrip("/")
        self.api_key: str = entry.data.get(CONF_API_KEY, "")
        self.entities_config: list[dict] = []

        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    def _headers(self) -> dict:
        h = {"Accept": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    async def _api_get(self, path: str) -> Any:
        url = f"{self.host}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers(), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 401:
                    raise UpdateFailed("Authenticatie mislukt — controleer je API-sleutel in VUN-Tuya-Hassio")
                resp.raise_for_status()
                return await resp.json()

    async def _api_post(self, path: str, body: dict) -> Any:
        url = f"{self.host}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self._headers(), json=body, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def async_refresh_entities(self) -> None:
        """Haal alle bevestigde entities op via de discovery API (éénmalig bij setup)."""
        try:
            data = await self._api_get("/api/integration/discovery")
            self.entities_config = data.get("entities", [])
            _LOGGER.info("VUN Tuya: %d entities ontdekt", len(self.entities_config))
        except Exception as err:
            _LOGGER.error("Discovery mislukt: %s", err)
            raise

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Poll live DP status voor alle bekende devices — aangeroepen door HA."""
        if not self.entities_config:
            try:
                await self.async_refresh_entities()
            except Exception as err:
                raise UpdateFailed(f"Entities ophalen mislukt: {err}") from err

        device_ids = {e["device_id"] for e in self.entities_config}
        status: dict[str, dict[str, Any]] = {}

        for device_id in device_ids:
            try:
                result = await self._api_get(f"/api/devices/{device_id}/live_dps")
                dp_map: dict[str, Any] = {}
                for item in result.get("status", []):
                    dp_map[item["code"]] = item["value"]
                status[device_id] = dp_map
            except Exception as err:
                _LOGGER.debug("Live DPS mislukt voor %s: %s", device_id, err)
                status.setdefault(device_id, {})

        return status

    async def async_send_command(self, device_id: str, commands: list[dict]) -> bool:
        """Stuur commando's naar een device via de VUN-Tuya-Hassio API."""
        try:
            await self._api_post(
                f"/api/devices/{device_id}/command",
                {"commands": commands},
            )
            return True
        except Exception as err:
            _LOGGER.warning("Commando mislukt voor %s: %s", device_id, err)
            return False

    def get_entity_status(self, device_id: str, dp_code: str) -> Any:
        """Haal een specifieke DP waarde op uit de gecachte coordinator data."""
        if not self.data:
            return None
        return self.data.get(device_id, {}).get(dp_code)
