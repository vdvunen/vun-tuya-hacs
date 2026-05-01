"""DataUpdateCoordinator voor VUN Tuya — combineert Cloud sync en lokale polling."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import timedelta
from typing import Any, Optional

import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_REGION,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_COUNTRY_CODE,
    CONF_SCAN_INTERVAL,
    CONF_SUBNET,
    CONF_SCAN_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_TIMEOUT,
    DOMAIN,
    TUYA_REGION_URLS,
)

_LOGGER = logging.getLogger(__name__)


class VunTuyaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """
    Centraal data-update punt voor alle VUN Tuya devices.

    data structuur na update:
    {
        "<device_id>": {
            "id": str,
            "name": str,
            "category": str,
            "online": bool,
            "ip": str | None,
            "local_key": str,
            "version": str,
            "status": [{"code": str, "value": any}, ...],
        },
        ...
    }
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api_key: str = entry.data[CONF_API_KEY]
        self.api_secret: str = entry.data[CONF_API_SECRET]
        self.region: str = entry.data[CONF_REGION]
        self.username: str = entry.data.get(CONF_USERNAME, "")
        self.password: str = entry.data.get(CONF_PASSWORD, "")
        self.country_code: str = entry.data.get(CONF_COUNTRY_CODE, "31")
        self.base_url: str = TUYA_REGION_URLS[self.region]

        self._access_token: Optional[str] = None
        self._token_expires: float = 0

        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    # ── Authenticatie ──────────────────────────────────────────────────────────

    def _sign(self, access_token: str, string_to_sign: str, t: str) -> str:
        msg = self.api_key + access_token + t + string_to_sign
        return hmac.new(
            self.api_secret.encode(), msg=msg.encode(), digestmod=hashlib.sha256
        ).hexdigest().upper()

    def _build_headers(self, method: str, path: str, body: dict | None = None) -> dict:
        t = str(int(time.time() * 1000))
        token = self._access_token or ""
        body_bytes = json.dumps(body, separators=(",", ":")).encode() if body else b""
        content_hash = hashlib.sha256(body_bytes).hexdigest()
        sts = "\n".join([method.upper(), content_hash, "", path])
        sign = self._sign(token, sts, t)
        return {
            "client_id": self.api_key,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "access_token": token,
        }

    def _get_token_sync(self) -> Optional[str]:
        """Haal een access token op (blocking, wordt via executor aangeroepen)."""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        path = "/v1.0/token?grant_type=1"
        t = str(int(time.time() * 1000))
        content_hash = hashlib.sha256(b"").hexdigest()
        sts = "\n".join(["GET", content_hash, "", path])
        sign = self._sign("", sts, t)

        try:
            resp = httpx.get(
                f"{self.base_url}{path}",
                headers={
                    "client_id": self.api_key,
                    "sign": sign,
                    "t": t,
                    "sign_method": "HMAC-SHA256",
                    "access_token": "",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("success"):
                result = data["result"]
                self._access_token = result["access_token"]
                self._token_expires = time.time() + result.get("expire_time", 7200) - 60
                return self._access_token
            _LOGGER.error("Tuya token mislukt: %s %s", data.get("code"), data.get("msg"))
        except Exception as err:
            _LOGGER.error("Token request mislukt: %s", err)
        return None

    def _request_sync(self, method: str, path: str, body: dict | None = None) -> Optional[dict]:
        """Voer een Tuya Cloud API request uit (blocking)."""
        if not self._get_token_sync():
            return None
        headers = self._build_headers(method, path, body)
        try:
            resp = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=body,
                timeout=15,
            )
            data = resp.json()
            if data.get("success"):
                return data.get("result")
            _LOGGER.debug("API fout %s %s: %s", method, path, data.get("msg"))
        except Exception as err:
            _LOGGER.warning("API request mislukt %s %s: %s", method, path, err)
        return None

    # ── Device ophalen ─────────────────────────────────────────────────────────

    def _fetch_devices_sync(self) -> list[dict]:
        """Haal alle devices op via Tuya Cloud (meerdere strategieën)."""
        # Strategie 1: tinytuya Cloud class
        devices = self._fetch_via_tinytuya()
        if devices:
            _LOGGER.debug("Devices via tinytuya: %d", len(devices))
            return devices

        # Strategie 2: IoT Core API
        devices = self._fetch_via_iot_core()
        if devices:
            _LOGGER.debug("Devices via IoT Core: %d", len(devices))
            return devices

        _LOGGER.warning("Geen devices gevonden via Cloud API")
        return []

    def _fetch_via_tinytuya(self) -> list[dict]:
        """Gebruik de tinytuya Cloud class om devices op te halen."""
        try:
            import tinytuya

            cloud = tinytuya.Cloud(
                apiKey=self.api_key,
                apiSecret=self.api_secret,
                apiRegion=self.region,
                apiDeviceID="x",
            )
            result = cloud.getdevices(verbose=True)
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "devices" in result:
                return result["devices"]
        except Exception as err:
            _LOGGER.debug("tinytuya Cloud mislukt: %s", err)
        return []

    def _fetch_via_iot_core(self) -> list[dict]:
        """Haal devices op via de IoT Core API."""
        result = self._request_sync("GET", "/v1.3/iot-03/devices?page_size=50")
        if not result:
            return []
        devices = []
        for item in result.get("devices") or result.get("list") or []:
            devices.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "online": item.get("online", False),
                "local_key": item.get("local_key", ""),
                "ip": item.get("ip"),
                "model": item.get("model", ""),
                "product_name": item.get("product_name", ""),
            })
        return devices

    def _get_device_status_sync(self, device_id: str) -> list[dict]:
        """Haal de huidige status van een device op via Cloud."""
        result = self._request_sync("GET", f"/v1.0/iot-03/devices/{device_id}/status")
        if not result:
            return []
        return result if isinstance(result, list) else []

    # ── Lokale status polling ──────────────────────────────────────────────────

    def _get_status_local_sync(self, device: dict) -> list[dict]:
        """Haal status op via lokaal LAN (tinytuya)."""
        ip = device.get("ip")
        local_key = device.get("local_key", "")
        device_id = device.get("id", "")
        version = float(device.get("version") or "3.3")

        if not ip or not local_key:
            return []

        try:
            import tinytuya

            d = tinytuya.Device(
                dev_id=device_id,
                address=ip,
                local_key=local_key,
                version=version,
            )
            d.set_socketTimeout(5)
            d.set_socketRetryLimit(1)
            data = d.status()

            if not data or data.get("Error"):
                return []

            dps = data.get("dps") or {}
            return [{"code": f"dp_{k}", "value": v} for k, v in dps.items()]
        except Exception as err:
            _LOGGER.debug("Lokale status mislukt %s (%s): %s", device.get("name"), ip, err)
            return []

    # ── DataUpdateCoordinator interface ────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        """Haal data op — wordt periodiek door HA aangeroepen."""
        try:
            devices_raw = await self.hass.async_add_executor_job(
                self._fetch_devices_sync
            )
        except Exception as err:
            raise UpdateFailed(f"Tuya Cloud sync mislukt: {err}") from err

        data: dict[str, Any] = {}
        for dev in devices_raw:
            device_id = dev.get("id") or dev.get("uuid")
            if not device_id:
                continue

            # Probeer lokale status, val terug op Cloud status
            status: list[dict] = []
            ip = dev.get("ip")
            local_key = dev.get("local_key", "")
            if ip and local_key:
                status = await self.hass.async_add_executor_job(
                    self._get_status_local_sync, dev
                )

            if not status:
                status = await self.hass.async_add_executor_job(
                    self._get_device_status_sync, device_id
                )

            data[device_id] = {
                "id": device_id,
                "name": dev.get("name", device_id),
                "category": dev.get("category", ""),
                "online": dev.get("online", False),
                "ip": ip,
                "local_key": local_key,
                "version": str(dev.get("version") or "3.3"),
                "model": dev.get("model", ""),
                "product_name": dev.get("product_name", ""),
                "status": status,
            }

        if not data:
            raise UpdateFailed("Geen Tuya devices gevonden — controleer je API credentials")

        return data

    # ── Commando's sturen ──────────────────────────────────────────────────────

    async def async_send_command(
        self, device_id: str, commands: list[dict]
    ) -> bool:
        """
        Stuur commando's naar een device.

        Probeert eerst lokaal (LAN), val terug op Cloud API.
        commands: [{"code": "switch_led", "value": True}, ...]
        """
        device = self.data.get(device_id) if self.data else None
        if not device:
            _LOGGER.warning("Device %s niet gevonden in coordinator data", device_id)
            return False

        # Lokaal proberen
        if device.get("ip") and device.get("local_key"):
            success = await self.hass.async_add_executor_job(
                self._send_command_local_sync, device, commands
            )
            if success:
                return True

        # Cloud fallback
        return await self.hass.async_add_executor_job(
            self._send_command_cloud_sync, device_id, commands
        )

    def _send_command_local_sync(self, device: dict, commands: list[dict]) -> bool:
        """Stuur commando's via lokaal LAN (blocking)."""
        try:
            import tinytuya

            d = tinytuya.Device(
                dev_id=device["id"],
                address=device["ip"],
                local_key=device["local_key"],
                version=float(device.get("version") or "3.3"),
            )
            d.set_socketTimeout(5)
            d.set_socketRetryLimit(1)

            payload = {cmd["code"]: cmd["value"] for cmd in commands}
            result = d.set_multiple_values(payload, nowait=True)

            if isinstance(result, dict) and result.get("Error"):
                _LOGGER.debug("Lokaal commando fout %s: %s", device["name"], result["Error"])
                return False

            _LOGGER.debug("Lokaal commando OK: %s %s", device["name"], payload)
            return True
        except Exception as err:
            _LOGGER.debug("Lokaal commando mislukt %s: %s", device.get("name"), err)
            return False

    def _send_command_cloud_sync(self, device_id: str, commands: list[dict]) -> bool:
        """Stuur commando's via Tuya Cloud API (blocking)."""
        path = f"/v1.0/iot-03/devices/{device_id}/commands"
        body = {"commands": commands}
        result = self._request_sync("POST", path, body)
        if result is not None:
            _LOGGER.debug("Cloud commando OK: %s %s", device_id, commands)
            return True
        _LOGGER.warning("Cloud commando mislukt: %s %s", device_id, commands)
        return False

    def get_device_status_value(self, device_id: str, code: str) -> Any:
        """Haal de waarde van een specifieke DP code op uit de gecachte data."""
        if not self.data:
            return None
        device = self.data.get(device_id)
        if not device:
            return None
        for item in device.get("status") or []:
            if item.get("code") == code:
                return item.get("value")
        return None
