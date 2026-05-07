"""Config flow voor de VUN Tuya integratie."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_API_KEY, CONF_HOST, CONF_SCAN_INTERVAL, DEFAULT_HOST, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Optional(CONF_API_KEY, default=""): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=10, max=300)
        ),
    }
)


class VunTuyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Afhandeling van de VUN Tuya config flow."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            api_key = user_input.get(CONF_API_KEY, "").strip()

            # Normaliseer host (voeg http:// toe als ontbreekt)
            if not host.startswith(("http://", "https://")):
                host = f"http://{host}"

            valid, error = await self._test_connection(host, api_key)
            if valid:
                parsed = urlparse(host)
                await self.async_set_unique_id(f"vun_tuya_{parsed.netloc}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"VUN Tuya ({parsed.netloc})",
                    data={CONF_HOST: host, CONF_API_KEY: api_key},
                    options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={"default_host": DEFAULT_HOST},
        )

    async def _test_connection(self, host: str, api_key: str) -> tuple[bool, str]:
        """Test de verbinding met de VUN-Tuya-Hassio server."""
        headers = {"Accept": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{host}/api/integration/discovery",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        return False, "invalid_auth"
                    if resp.status == 404:
                        return False, "endpoint_not_found"
                    resp.raise_for_status()
                    return True, ""
        except aiohttp.ClientConnectorError:
            return False, "cannot_connect"
        except Exception as err:
            _LOGGER.warning("Verbindingstest mislukt: %s", err)
            return False, "cannot_connect"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VunTuyaOptionsFlow:
        return VunTuyaOptionsFlow(config_entry)


class VunTuyaOptionsFlow(config_entries.OptionsFlow):
    """Opties flow voor polling interval."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=10, max=300)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
