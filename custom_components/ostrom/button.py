"""Button platform for Ostrom integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OstromCoordinator


class OstromRefreshDataButton(CoordinatorEntity[OstromCoordinator], ButtonEntity):
    """Button to trigger an immediate data refresh."""

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)

        self._attr_unique_id = "ostrom_refresh_data"
        self._attr_name = "Ostrom Refresh Data"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared device metadata so entities are grouped in one device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "integration")},
            name="Ostrom",
            manufacturer="Ostrom",
            model="Dynamic Tariff Integration",
        )


async def async_setup_entry(
    _: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up button entities for Ostrom integration."""

    coordinator: OstromCoordinator = config_entry.runtime_data
    async_add_entities([OstromRefreshDataButton(coordinator)])
