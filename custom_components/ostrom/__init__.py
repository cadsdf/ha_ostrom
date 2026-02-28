"""Ostrom electricity provider Configuration with contract selection.

This file is the entry point of Home Assistant custom component for Ostrom electricity provider.

Note on linter import order:

Imports are ordered as:
1. future imports (compiler directives)
2. standard library imports
3. third party imports
4. local application/library specific imports

Each group is separated by a blank line.
Both import and from statements within a group are ordered alphabetically.

show issues with
ruff check <file> --select I

auto fix using
ruff check <file> --select I --fix
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .const import DOMAIN, SERVICE_REFRESH_DATA

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall
    from .coordinator import OstromCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: tuple[str, ...] = ("sensor", "button")


def _get_runtime_store(hass: HomeAssistant) -> dict[str, Any]:
    """Return the integration runtime store."""
    return hass.data.setdefault(DOMAIN, {})


async def _async_handle_refresh_data_service(hass: HomeAssistant, _: ServiceCall) -> None:
    """Handle manual refresh requests for all loaded Ostrom entries."""
    coordinators = list(_get_runtime_store(hass).values())

    if not coordinators:
        _LOGGER.debug("Refresh service called with no active Ostrom entries")
        return

    _LOGGER.debug("Manual refresh requested for %s Ostrom entr(y/ies)", len(coordinators))

    for coordinator in coordinators:
        await coordinator.async_request_refresh()


async def async_setup(hass: HomeAssistant, _: dict[str, Any]) -> bool:
    """Set up the Ostrom integration domain."""
    _get_runtime_store(hass)

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA):

        async def async_handle_refresh_data(call: ServiceCall) -> None:
            """Forward the refresh service call to the shared handler."""
            await _async_handle_refresh_data_service(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_DATA,
            async_handle_refresh_data,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config."""
    # Import lazily so standalone scripts can import package submodules
    # without requiring Home Assistant to be installed.
    from .coordinator import OstromCoordinator

    coordinator = OstromCoordinator(hass, entry)

    _LOGGER.debug("Setting up Ostrom integration")

    # Set up regular update tasks
    await coordinator.async_setup_hourly_update()

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Keep coordinator available for services and unload handling
    _get_runtime_store(hass)[entry.entry_id] = coordinator

    # Make the coordinator available to other parts of the integration
    entry.runtime_data = coordinator

    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, list(PLATFORMS))

    _LOGGER.debug("Ostrom integration setup complete")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Note: runtime_data cleanup is automatic, no need to manually clean hass.data
    """

    _LOGGER.debug("Unloading Ostrom integration")

    # Unload platforms
    unloaded = await hass.config_entries.async_unload_platforms(entry, list(PLATFORMS))

    if unloaded:
        coordinator: OstromCoordinator = entry.runtime_data
        await coordinator.async_shutdown()

        runtime_store = _get_runtime_store(hass)
        runtime_store.pop(entry.entry_id, None)

        if not runtime_store and hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA):
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)

    return unloaded
