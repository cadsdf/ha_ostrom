"""Tests for Ostrom coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from custom_components.ostrom.coordinator import OstromCoordinator
from custom_components.ostrom.ostrom_error import OstromError


async def test_coordinator_update_success(hass, mock_config_entry, sample_consumer_data) -> None:
    """Coordinator should store and return fresh consumer data on successful update."""
    coordinator = OstromCoordinator(hass, mock_config_entry)

    coordinator.provider.initialize = AsyncMock(return_value=None)
    coordinator.provider.update_data = AsyncMock(return_value=None)
    coordinator.provider.get_consumer_data = Mock(return_value=sample_consumer_data)

    data = await coordinator._async_update_data()

    assert data.ok is True
    assert coordinator.get_data() is data


async def test_coordinator_update_failure_sets_error(hass, mock_config_entry) -> None:
    """Coordinator should preserve data object and set error on provider failure."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator._provider_initialized = True

    coordinator.provider.update_data = AsyncMock(return_value=OstromError("boom"))

    data = await coordinator._async_update_data()

    assert data.ok is False
    assert data.error is not None
    assert "API error" in data.error
