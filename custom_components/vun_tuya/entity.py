"""Basis entity klasse voor VUN Tuya integratie."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VunTuyaCoordinator


class VunTuyaEntity(CoordinatorEntity[VunTuyaCoordinator]):
    """Basis entity die de coordinator data deelt."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VunTuyaCoordinator,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = device_id

    @property
    def _device_data(self) -> dict[str, Any]:
        """Geeft de ruwe device data uit de coordinator terug."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._device_id) or {}
        return {}

    @property
    def available(self) -> bool:
        """Geeft True terug als het device online en bereikbaar is."""
        return self.coordinator.last_update_success and bool(
            self._device_data.get("online", False)
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Geeft device informatie terug voor het device registry."""
        data = self._device_data
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=data.get("name", self._device_id),
            manufacturer="Tuya",
            model=data.get("product_name") or data.get("model") or data.get("category"),
            sw_version=data.get("version"),
        )

    def _get_dp_value(self, *codes: str) -> Any:
        """
        Haal de waarde op van de eerste DP code die aanwezig is in de status.

        Accepteert meerdere codes zodat je primaire en fallback codes kunt opgeven.
        """
        status: list[dict] = self._device_data.get("status") or []
        status_map = {item["code"]: item["value"] for item in status}
        for code in codes:
            if code in status_map:
                return status_map[code]
        return None

    async def _async_send(self, commands: list[dict]) -> None:
        """Stuur commando's en verzoek daarna een coordinator update."""
        await self.coordinator.async_send_command(self._device_id, commands)
        await self.coordinator.async_request_refresh()
