"""Config flow voor de VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
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
    DEFAULT_SUBNET,
    DEFAULT_SCAN_TIMEOUT,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_REGION,
    TUYA_REGIONS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_API_SECRET): str,
        vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(TUYA_REGIONS),
        vol.Optional(CONF_USERNAME, default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=10, max=300)
        ),
        vol.Optional(CONF_SUBNET, default=DEFAULT_SUBNET): str,
        vol.Optional(CONF_SCAN_TIMEOUT, default=DEFAULT_SCAN_TIMEOUT): vol.All(
            int, vol.Range(min=2, max=30)
        ),
    }
)


class VunTuyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Afhandeling van de VUN Tuya config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Verwerk de initiële gebruikersinvoer."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            api_secret = user_input[CONF_API_SECRET].strip()

            if not api_key:
                errors[CONF_API_KEY] = "api_key_required"
            elif not api_secret:
                errors[CONF_API_SECRET] = "api_secret_required"
            else:
                await self.async_set_unique_id(api_key)
                self._abort_if_unique_id_configured()

                valid = await self._test_credentials(
                    api_key,
                    api_secret,
                    user_input[CONF_REGION],
                )
                if valid:
                    return self.async_create_entry(
                        title=f"VUN Tuya ({user_input[CONF_REGION].upper()})",
                        data=user_input,
                        options={
                            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                            CONF_SUBNET: DEFAULT_SUBNET,
                            CONF_SCAN_TIMEOUT: DEFAULT_SCAN_TIMEOUT,
                        },
                    )
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "cloud_url": "iot.tuya.com",
            },
        )

    async def _test_credentials(
        self, api_key: str, api_secret: str, region: str
    ) -> bool:
        """Test de Tuya Cloud credentials door een token op te halen."""
        try:
            import hashlib
            import hmac
            import json
            import time

            import httpx

            from .const import TUYA_REGION_URLS

            base_url = TUYA_REGION_URLS[region]
            path = "/v1.0/token?grant_type=1"
            t = str(int(time.time() * 1000))
            content_hash = hashlib.sha256(b"").hexdigest()
            sts = "\n".join(["GET", content_hash, "", path])
            msg = api_key + "" + t + sts
            sign = hmac.new(
                api_secret.encode(), msg=msg.encode(), digestmod=hashlib.sha256
            ).hexdigest().upper()

            resp = await self.hass.async_add_executor_job(
                lambda: httpx.get(
                    f"{base_url}{path}",
                    headers={
                        "client_id": api_key,
                        "sign": sign,
                        "t": t,
                        "sign_method": "HMAC-SHA256",
                    },
                    timeout=10,
                )
            )
            data = resp.json()
            return bool(data.get("success"))
        except Exception as err:
            _LOGGER.warning("Credential test mislukt: %s", err)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VunTuyaOptionsFlow:
        """Geef de options flow terug."""
        return VunTuyaOptionsFlow(config_entry)


class VunTuyaOptionsFlow(config_entries.OptionsFlow):
    """Afhandeling van de VUN Tuya options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Verwerk de opties."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=10, max=300)),
                vol.Optional(
                    CONF_SUBNET,
                    default=current.get(CONF_SUBNET, DEFAULT_SUBNET),
                ): str,
                vol.Optional(
                    CONF_SCAN_TIMEOUT,
                    default=current.get(CONF_SCAN_TIMEOUT, DEFAULT_SCAN_TIMEOUT),
                ): vol.All(int, vol.Range(min=2, max=30)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
