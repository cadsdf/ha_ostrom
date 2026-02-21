"""Update coordinator for Ostrom data."""

import logging
from datetime import UTC, datetime, timedelta
from typing import NoReturn

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, KEY_CONTRACT_ID, KEY_PASSWORD, KEY_USER, KEY_ZIP_CODE
from .ostrom_data import OstromConsumerData, OstromSpotPrice
from .ostrom_error import OstromError
from .ostrom_provider import OstromProvider

LOGGER = logging.getLogger(__name__)


def _raise_auth_failed(error: OstromError) -> NoReturn:
    """Raise an authentication failure."""
    raise ConfigEntryAuthFailed(f"Authentication failed: {error}") from error.exception


def _raise_update_failed(message: str, error: OstromError) -> NoReturn:
    """Raise a coordinator update failure."""
    raise UpdateFailed(message) from error.exception


def _raise_initialization_failed(error: OstromError) -> NoReturn:
    """Raise initialization failure with proper Home Assistant exception type."""
    if (
        isinstance(error.exception, aiohttp.ClientResponseError)
        and error.exception.status == 401
    ):
        _raise_auth_failed(error)

    _raise_update_failed(f"Provider initialization failed: {error}", error)


def _raise_provider_api_failed(error: OstromError) -> NoReturn:
    """Raise provider API failure with proper Home Assistant exception type."""
    if (
        isinstance(error.exception, aiohttp.ClientResponseError)
        and error.exception.status == 401
    ):
        _raise_auth_failed(error)

    _raise_update_failed(f"API error: {error}", error)


class OstromCoordinator(DataUpdateCoordinator):
    """Coordinator for Ostrom data."""

    FAIL_RETRY_INTERVAL_MINUTES: int = 10

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Load settings from config entry
        self.user: str = config_entry.data.get(KEY_USER)
        self.password: str = config_entry.data.get(KEY_PASSWORD)
        self.zip_code: str = config_entry.data.get(KEY_ZIP_CODE)

        self.contract_id: str = config_entry.data.get(KEY_CONTRACT_ID)

        # Initialize Ostrom API client
        self.provider = OstromProvider(
            user=self.user,
            password=self.password,
            endpoint_auth=None,  # Uses production defaults
            endpoint_data=None,
            zip_code=self.zip_code,
            contract_id=self.contract_id,
        )

        self.data: OstromConsumerData = OstromConsumerData()
        self._provider_initialized: bool = False

        # Init base DataUpdateCoordinator and pass update method
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
        )

        self._hass = hass

    def get_data(self) -> OstromConsumerData:
        """Get latest data."""

        if self.data is None:
            return OstromConsumerData(ok=False, error="No data available")

        return self.data

    async def _async_update_data(self) -> OstromConsumerData:
        """Login and fetch data from the provider."""

        try:
            # initialize provider once to update credentials, fetch user data and contracts
            if not self._provider_initialized:
                init_error = await self.provider.initialize()

                if init_error:
                    _raise_initialization_failed(init_error)

                self._provider_initialized = True

            # Call provider.update() to refresh all data
            error: OstromError | None = await self.provider.update_data()

            if error:
                _raise_provider_api_failed(error)

            # Get structured consumer data
            consumer_data: OstromConsumerData | None = self.provider.get_consumer_data()

            if not consumer_data:
                current = self.get_data()
                current.error = "Failed to fetch consumer data"
                current.ok = False

                return current

        except UpdateFailed as err:
            # Calculate retry time for logging
            retry_time = (
                datetime.now(tz=UTC)
                + timedelta(minutes=OstromCoordinator.FAIL_RETRY_INTERVAL_MINUTES)
            ).strftime("%H:%M")

            LOGGER.error(
                "API update failed, retrying in %s minutes at %s: %s",
                OstromCoordinator.FAIL_RETRY_INTERVAL_MINUTES,
                retry_time,
                err,
            )

            delay: timedelta = timedelta(
                minutes=OstromCoordinator.FAIL_RETRY_INTERVAL_MINUTES
            )

            # Schedule retry update
            async_call_later(self._hass, delay.total_seconds(), self._retry_update)

            current = self.get_data()
            current.ok = False
            current.error = str(err)

            return current
        else:
            consumer_data.ok = True
            consumer_data.error = None
            self.data = consumer_data

            return consumer_data

    async def _retry_update(self, _) -> None:
        """Retry update after failure."""

        LOGGER.info("Retrying API update after failure")

        await self.async_refresh()

    def _price_to_dict(
        self, price: OstromSpotPrice | None
    ) -> dict[str, str | float] | None:
        """Convert OstromSpotPrice to dict."""
        if not price:
            return None

        total = price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh

        return {
            "date": price.date.isoformat(),
            "total_price": total,
        }

    def _build_forecast(self) -> list[dict[str, str | float]]:
        """Build forecast list from spot prices."""
        if not self.provider.spot_prices:
            return []

        forecast: list[dict[str, str | float]] = []

        for price in self.provider.spot_prices:
            total = (
                price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh
            )

            forecast.append(
                {
                    "datetime": price.date.isoformat(),
                    "value": total,
                }
            )

        return forecast

    def _get_price_value(self, price: OstromSpotPrice | None) -> float | None:
        """Get total price value from OstromSpotPrice."""
        if not price:
            return None

        return price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh

    def _get_price_time(self, price: OstromSpotPrice | None) -> str | None:
        """Get datetime from OstromSpotPrice."""
        if not price:
            return None

        return price.date.isoformat()

    async def async_setup_hourly_update(self):
        """Set up hourly update at minute 1."""

        async def hourly_update(_):
            LOGGER.debug("Triggering hourly update at minute 1")

            await self._async_update_data()

        # Schedule update at minute 1 every hour
        async_track_time_change(
            self._hass,
            hourly_update,
            minute=1,
            second=0,
        )
