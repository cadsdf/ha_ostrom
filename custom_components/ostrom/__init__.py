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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from .coordinator import OstromCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: tuple[str, ...] = ("sensor", "button")


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

    return unloaded
