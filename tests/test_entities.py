"""Tests for Ostrom entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.ostrom.button import OstromRefreshDataButton
from custom_components.ostrom.coordinator import OstromCoordinator
from custom_components.ostrom.sensor import (
    OstromForecastSensor,
    OstromMonthlyBaseFeeSensor,
    OstromStatusSensor,
)

pytestmark = pytest.mark.asyncio


async def test_forecast_sensor_exposes_compatibility_data(
    hass, mock_config_entry, sample_consumer_data
) -> None:
    """Forecast sensor should expose both forecast and compatibility data payloads."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator.data = sample_consumer_data

    sensor = OstromForecastSensor(coordinator)
    attrs = sensor.extra_state_attributes

    assert "forecast" in attrs
    assert "data" in attrs
    assert attrs["data"][0]["date"] == attrs["forecast"][0]["datetime"]


async def test_monthly_base_fee_sensor_has_2_decimal_precision(
    hass, mock_config_entry, sample_consumer_data
) -> None:
    """Monthly base fee should request 2-digit display precision."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator.data = sample_consumer_data

    sensor = OstromMonthlyBaseFeeSensor(coordinator)

    assert sensor.suggested_display_precision == 2


async def test_refresh_button_triggers_coordinator_refresh(
    hass, mock_config_entry
) -> None:
    """Button press should call coordinator refresh."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator.async_request_refresh = AsyncMock()

    button = OstromRefreshDataButton(coordinator)
    await button.async_press()

    coordinator.async_request_refresh.assert_awaited_once()


async def test_entities_remain_available_after_update_failure(
    hass, mock_config_entry, sample_consumer_data
) -> None:
    """Sensors should keep stale values available while status reports an error."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator.data = sample_consumer_data
    coordinator.last_update_success = False
    coordinator.data.ok = False
    coordinator.data.error = "API error: boom"

    status = OstromStatusSensor(coordinator)
    sensor = OstromMonthlyBaseFeeSensor(coordinator)

    assert status.available is True
    assert status.native_value == "Error"
    assert sensor.available is True
    assert sensor.native_value == 6.0


async def test_refresh_button_remains_available_after_update_failure(
    hass, mock_config_entry
) -> None:
    """Manual refresh should remain pressable after coordinator update failures."""
    coordinator = OstromCoordinator(hass, mock_config_entry)
    coordinator.last_update_success = False

    button = OstromRefreshDataButton(coordinator)

    assert button.available is True
