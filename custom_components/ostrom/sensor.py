"""Sensor platform for Ostrom integration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, UNIT_EURO_PER_KWH
from .coordinator import OstromCoordinator
from .ostrom_data import OstromConsumerData, OstromSpotPrice


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _round2(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def _total_price_eur_per_kwh(spot_price: OstromSpotPrice | None) -> float | None:
    if not spot_price:
        return None

    return _round4(
        spot_price.price_gross_euro_per_kwh
        + spot_price.tax_and_levies_gross_euro_per_kwh
    )


def _entity_slug(sensor: str) -> str:
    return f"ostrom_{sensor}"


class OstromBaseEntity(CoordinatorEntity[OstromCoordinator]):
    """Base class for all Ostrom entities."""

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared device metadata so entities are grouped in one device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "integration")},
            name="Ostrom",
            manufacturer="Ostrom",
            model="Dynamic Tariff Integration",
        )

    @property
    def data(self) -> OstromConsumerData:
        """Return typed coordinator data."""
        data = self.coordinator.get_data()
        return (
            data if data is not None else OstromConsumerData(ok=False, error="No data")
        )

    def _set_identity(self, sensor: str, name: str) -> None:
        self._attr_unique_id = _entity_slug(sensor)
        self._attr_name = f"Ostrom {name}"


class OstromStatusSensor(OstromBaseEntity, SensorEntity):
    """Sensor to show integration health."""

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator)
        self._set_identity("status", "Status")
        self._attr_icon = "mdi:cloud-alert"

    @property
    def native_value(self) -> str:
        """Return the overall integration status."""
        return "OK" if self.data.ok else "Error"

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return status details."""
        timestamp = self.data.timestamp.isoformat() if self.data.timestamp else None
        return {
            "error": self.data.error,
            "timestamp": timestamp,
        }


class OstromCurrentElectricityPriceSensor(OstromBaseEntity, SensorEntity):
    """Current total electricity price (energy + taxes/levies)."""

    _attr_native_unit_of_measurement = UNIT_EURO_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the current electricity price sensor."""
        super().__init__(coordinator)
        self._set_identity("electricity_price", "Current Electricity Price")
        self._attr_icon = "mdi:currency-eur"

    @property
    def native_value(self) -> float | None:
        """Return the current total electricity price."""
        return _total_price_eur_per_kwh(self.data.spot_price_now)


class OstromCurrentNetEnergyPriceSensor(OstromBaseEntity, SensorEntity):
    """Current net energy-only price."""

    _attr_native_unit_of_measurement = UNIT_EURO_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the current net energy price sensor."""
        super().__init__(coordinator)
        self._set_identity("net_energy_price", "Current Net Energy Price")
        self._attr_icon = "mdi:flash"

    @property
    def native_value(self) -> float | None:
        """Return the current net energy price per kWh."""
        if not self.data.spot_price_now:
            return None
        return _round4(self.data.spot_price_now.price_net_euro_per_kwh)


class OstromCurrentTaxesAndLeviesSensor(OstromBaseEntity, SensorEntity):
    """Current taxes and levies component."""

    _attr_native_unit_of_measurement = UNIT_EURO_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the taxes and levies sensor."""
        super().__init__(coordinator)
        self._set_identity("taxes_and_levies", "Current Taxes And Levies")
        self._attr_icon = "mdi:receipt"

    @property
    def native_value(self) -> float | None:
        """Return current taxes and levies per kWh."""
        if not self.data.spot_price_now:
            return None
        return _round4(self.data.spot_price_now.tax_and_levies_gross_euro_per_kwh)


class OstromForecastSensor(OstromBaseEntity, SensorEntity):
    """Forecast carrier sensor for chart cards."""

    _attr_native_unit_of_measurement = UNIT_EURO_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the forecast sensor."""
        super().__init__(coordinator)
        self._set_identity("forecast", "Forecast")
        self._attr_icon = "mdi:chart-timeline-variant"

    @property
    def native_value(self) -> float | None:
        """Return the current total price used as sensor state."""
        return _total_price_eur_per_kwh(self.data.spot_price_now)

    @property
    def extra_state_attributes(self) -> dict:
        """Return forecast and minimum-price attributes."""
        attrs: dict = {}

        if not self.data.spot_prices:
            return attrs

        forecast = [
            {
                "datetime": item.date.isoformat(),
                "value": _total_price_eur_per_kwh(item),
            }
            for item in self.data.spot_prices
        ]

        attrs["forecast"] = forecast
        # Compatibility for cards expecting `attributes.data` with date/price keys.
        attrs["data"] = [
            {"date": item["datetime"], "price": item["value"]} for item in forecast
        ]

        attrs["minimum_price_today"] = _price_to_dict(
            self.data.spot_price_minimum_today
        )

        attrs["minimum_price_upcoming_today"] = _price_to_dict(
            self.data.spot_price_minimum_remaining_today
        )

        attrs["minimum_price_tomorrow"] = _price_to_dict(
            self.data.spot_price_minimum_tomorrow
        )

        attrs["minimum_price_all_available"] = _price_to_dict(
            self.data.spot_price_minimum_all_available
        )

        attrs["lowest_price"] = _total_price_eur_per_kwh(
            self.data.spot_price_minimum_remaining_today
        )

        attrs["lowest_price_time"] = (
            self.data.spot_price_minimum_remaining_today.date.isoformat()
            if self.data.spot_price_minimum_remaining_today
            else None
        )

        if forecast:
            attrs["forecast_count"] = len(forecast)
            attrs["forecast_first"] = forecast[0]["datetime"]
            attrs["forecast_last"] = forecast[-1]["datetime"]

            now = datetime.now(tz=UTC)

            attrs["forecast_future_count"] = sum(
                1
                for item in forecast
                if datetime.fromisoformat(str(item["datetime"])) >= now
            )

        return attrs


class OstromMonthlyBaseFeeSensor(OstromBaseEntity, SensorEntity):
    """Monthly fixed base fee."""

    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the monthly base fee sensor."""
        super().__init__(coordinator)

        self._set_identity("monthly_base_fee", "Monthly Base Fee")
        self._attr_icon = "mdi:cash-minus"

    @property
    def native_value(self) -> float | None:
        """Return the monthly base fee."""
        if not self.data.spot_price_now:
            return None

        return _round2(self.data.spot_price_now.base_fee_gross_euro_per_month)


class OstromMonthlyGridFeeSensor(OstromBaseEntity, SensorEntity):
    """Monthly grid fee."""

    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the monthly grid fee sensor."""
        super().__init__(coordinator)

        self._set_identity("monthly_grid_fee", "Monthly Grid Fee")
        self._attr_icon = "mdi:transmission-tower"

    @property
    def native_value(self) -> float | None:
        """Return the monthly grid fee."""
        if not self.data.spot_price_now:
            return None

        return _round2(self.data.spot_price_now.grid_fees_gross_euro_per_month)


class OstromMonthlyFeesSensor(OstromBaseEntity, SensorEntity):
    """Monthly fixed fees (base + grid)."""

    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the combined monthly fees sensor."""
        super().__init__(coordinator)

        self._set_identity("monthly_fees", "Monthly Fees")
        self._attr_icon = "mdi:cash-multiple"

    @property
    def native_value(self) -> float | None:
        """Return total monthly fixed fees."""
        if not self.data.spot_price_now:
            return None

        return _round2(
            self.data.spot_price_now.base_fee_gross_euro_per_month
            + self.data.spot_price_now.grid_fees_gross_euro_per_month
        )


class OstromMinimumPriceSensor(OstromBaseEntity, SensorEntity):
    """Generic minimum-price sensor."""

    _attr_native_unit_of_measurement = UNIT_EURO_PER_KWH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(
        self,
        coordinator: OstromCoordinator,
        *,
        sensor: str,
        selector: Callable[[OstromConsumerData], OstromSpotPrice | None],
        name: str,
        icon: str,
    ) -> None:
        """Initialize a minimum-price sensor."""
        super().__init__(coordinator)
        self._selector = selector
        self._set_identity(sensor, name)
        self._attr_icon = icon

    @property
    def native_value(self) -> float | None:
        """Return the selected minimum price."""
        return _total_price_eur_per_kwh(self._selector(self.data))


class OstromMinimumPriceTimeSensor(OstromBaseEntity, SensorEntity):
    """Timestamp sensor for minimum-price targets."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: OstromCoordinator,
        *,
        sensor: str,
        selector: Callable[[OstromConsumerData], OstromSpotPrice | None],
        name: str,
        icon: str,
    ) -> None:
        """Initialize a minimum-price timestamp sensor."""
        super().__init__(coordinator)
        self._selector = selector
        self._set_identity(sensor, name)
        self._attr_icon = icon

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the selected minimum price."""
        price = self._selector(self.data)
        return price.date if price else None


class OstromLowestPriceNowBinary(OstromBaseEntity, BinarySensorEntity):
    """True when current price equals the upcoming minimum for today."""

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the lowest-price-now binary sensor."""
        super().__init__(coordinator)
        self._set_identity("lowest_price_is_now", "Lowest Price Is Now")
        self._attr_icon = "mdi:power-plug"

    @property
    def is_on(self) -> bool:
        """Return whether the current price is the upcoming daily minimum."""
        return bool(self.data.minimum_is_current_price)


def _price_to_dict(price: OstromSpotPrice | None) -> dict[str, str | float] | None:
    if not price:
        return None

    return {
        "date": price.date.isoformat(),
        "total_price": _total_price_eur_per_kwh(price),
    }


async def async_setup_entry(
    _: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up sensors for Ostrom integration."""

    coordinator: OstromCoordinator = config_entry.runtime_data

    entities = [
        OstromStatusSensor(coordinator),
        OstromCurrentElectricityPriceSensor(coordinator),
        OstromCurrentNetEnergyPriceSensor(coordinator),
        OstromCurrentTaxesAndLeviesSensor(coordinator),
        OstromForecastSensor(coordinator),
        OstromMonthlyBaseFeeSensor(coordinator),
        OstromMonthlyGridFeeSensor(coordinator),
        OstromMonthlyFeesSensor(coordinator),
        OstromMinimumPriceSensor(
            coordinator,
            sensor="minimum_price_today",
            name="Minimum Price Today",
            selector=lambda d: d.spot_price_minimum_today,
            icon="mdi:calendar-clock",
        ),
        OstromMinimumPriceSensor(
            coordinator,
            sensor="minimum_price_upcoming_today",
            name="Minimum Price Upcoming Today",
            selector=lambda d: d.spot_price_minimum_remaining_today,
            icon="mdi:calendar-arrow-right",
        ),
        OstromMinimumPriceSensor(
            coordinator,
            sensor="minimum_price_tomorrow",
            name="Minimum Price Tomorrow",
            selector=lambda d: d.spot_price_minimum_tomorrow,
            icon="mdi:weather-night",
        ),
        OstromMinimumPriceSensor(
            coordinator,
            sensor="minimum_price_all_available",
            name="Minimum Price All Available",
            selector=lambda d: d.spot_price_minimum_all_available,
            icon="mdi:chart-line",
        ),
        OstromMinimumPriceTimeSensor(
            coordinator,
            sensor="minimum_price_today_time",
            name="Minimum Price Today Time",
            selector=lambda d: d.spot_price_minimum_today,
            icon="mdi:clock-outline",
        ),
        OstromMinimumPriceTimeSensor(
            coordinator,
            sensor="minimum_price_upcoming_today_time",
            name="Minimum Price Upcoming Today Time",
            selector=lambda d: d.spot_price_minimum_remaining_today,
            icon="mdi:clock-outline",
        ),
        OstromMinimumPriceTimeSensor(
            coordinator,
            sensor="minimum_price_tomorrow_time",
            name="Minimum Price Tomorrow Time",
            selector=lambda d: d.spot_price_minimum_tomorrow,
            icon="mdi:clock-outline",
        ),
        OstromMinimumPriceTimeSensor(
            coordinator,
            sensor="minimum_price_all_available_time",
            name="Minimum Price All Available Time",
            selector=lambda d: d.spot_price_minimum_all_available,
            icon="mdi:clock-outline",
        ),
        OstromLowestPriceNowBinary(coordinator),
    ]

    async_add_entities(entities)
