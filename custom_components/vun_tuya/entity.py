"""Basis entity klasse voor VUN Tuya integratie."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VunTuyaCoordinator


class VunTuyaEntity(CoordinatorEntity[VunTuyaCoordinator]):
    """
    Basis entity — één VUN-Tuya-Hassio entity config → één HA entity.

    entity_config structuur (van de discovery API):
    {
        "id": "uuid",
        "device_id": "abc123",
        "device_name": "Woonkamerlamp",
        "entity_type": "light",
        "name": "Woonkamerlamp Licht",
        "friendly_name": "Woonkamerlamp",
        "entity_id": "light.woonkamerlamp",
        "ha_config": {...},
        "mappings": [{"dp_code": "switch_led", "dp_id": 20, "ha_attribute": "state"}, ...],
    }
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VunTuyaCoordinator,
        entity_config: dict,
    ) -> None:
        super().__init__(coordinator)
        self._entity_config = entity_config
        self._device_id: str = entity_config["device_id"]
        self._attr_unique_id = entity_config["id"]
        self._attr_name = entity_config.get("name") or None

        # Bouw mapping: ha_attribute → dp_code
        self._attr_map: dict[str, str] = {
            m["ha_attribute"]: m["dp_code"]
            for m in entity_config.get("mappings", [])
        }

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self._entity_config.get("device_online", True)
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._entity_config.get("device_name", self._device_id),
            manufacturer="Tuya",
        )

    def _get(self, ha_attribute: str) -> Any:
        """Geeft de huidige waarde van het gemapte DP code terug."""
        dp_code = self._attr_map.get(ha_attribute)
        if not dp_code:
            return None
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._device_id, {}).get(dp_code)

    def _dp_code(self, ha_attribute: str) -> str | None:
        """Geeft de DP code voor een HA attribuut terug."""
        return self._attr_map.get(ha_attribute)

    async def _send(self, commands: list[dict]) -> None:
        """Stuur commando's en vraag een coordinator update aan."""
        await self.coordinator.async_send_command(self._device_id, commands)
        await self.coordinator.async_request_refresh()

    async def _send_dp(self, ha_attribute: str, value: Any) -> None:
        """Stuur één DP commando via het gemapte attribuut."""
        code = self._dp_code(ha_attribute)
        if code:
            await self._send([{"code": code, "value": value}])
