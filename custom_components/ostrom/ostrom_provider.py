"""Ostrom electricity provider API integration."""

import logging
from datetime import UTC, datetime, timedelta

from .ostrom_api_client import OstromAPIClient
from .ostrom_data import (
    OstromConsumerData,
    OstromConsumption,
    OstromContract,
    OstromCustomerInfo,
    OstromSpotPrice,
    OstromUser,
)
from .ostrom_error import OstromError

_LOGGER = logging.getLogger(__name__)


class OstromProvider:
    """Ostrom data provider class."""

    def __init__(
        self,
        user: str,
        password: str,
        endpoint_auth: str | None = OstromAPIClient.ENDPOINT_PRODUCTION_AUTH,
        endpoint_data: str | None = OstromAPIClient.ENDPOINT_PRODUCTION_DATA,
        zip_code: str | None = None,
        contract_id: str | None = None,
    ) -> None:
        """Initialize."""
        self.expire = datetime.now(tz=UTC)

        self.client = OstromAPIClient(
            client_id=user,
            client_secret=password,
            endpoint_auth=endpoint_auth,
            endpoint_data=endpoint_data,
        )

        self.zip_code: str | None = zip_code
        self.contract_id: str | None = contract_id
        self.consumer_info: OstromCustomerInfo | None = None
        self.consumer_data: OstromConsumerData | None = None

    def set_zip_code(self, zip_code: str) -> None:
        """Zip code to use for spot price information requests."""
        self.zip_code = zip_code

    def set_contract_id(self, contract_id: str) -> None:
        """Contract ID to use for user contract information requests."""
        self.contract_id = contract_id

    async def initialize(self) -> OstromError | None:
        """Initialize the provider by refreshing the access token and fetching initial data."""
        error = await self._refresh_access_token()

        if error is not None:
            return error

        customer_info = await self._fetch_customer_info()

        if isinstance(customer_info, OstromError):
            return customer_info

        self.consumer_info = customer_info

        # Do not overwrite existing contract ID if already configured
        if (
            not self.contract_id
            and self.consumer_info.contracts
            and len(self.consumer_info.contracts) > 0
        ):
            self.contract_id = self.consumer_info.contracts[0].id

        return None

    async def update_data(self) -> OstromError | None:
        """Fetch and update the latest consumption and spot price data."""
        data = await self._fetch_data()

        if not data:
            return OstromError("Failed to fetch consumer data")

        self.consumer_data = data

        return None

    def get_user(self) -> OstromUser | None:
        """Get the user information."""
        return self.consumer_info.user if self.consumer_info else None

    def get_contracts(self) -> list[OstromContract] | None:
        """Get the list of user contracts."""
        return self.consumer_info.contracts if self.consumer_info else None

    def get_selected_contract(self) -> OstromContract | None:
        """Get the currently selected contract information."""
        if (
            not self.consumer_info
            or not self.consumer_info.contracts
            or not self.contract_id
        ):
            return None

        for contract in self.consumer_info.contracts:
            if contract.id == self.contract_id:
                return contract

        return None

    def get_consumer_data(self) -> OstromConsumerData | None:
        """Get the latest consumer data."""
        return self.consumer_data

    def get_consumption(self) -> list[OstromConsumption] | None:
        """Get the latest energy consumption data."""
        return self.consumer_data.consumptions if self.consumer_data else None

    def get_spot_prices(self) -> list[OstromSpotPrice] | None:
        """Get the latest spot price data."""
        return self.consumer_data.spot_prices if self.consumer_data else None

    async def _refresh_access_token(self) -> OstromError | None:
        """Authenticate and obtain an access token from Ostrom API.

        The default expiration time is 3600 seconds.
        """

        return await self.client.refresh_access_token()

    async def _fetch_customer_info(self) -> OstromCustomerInfo | OstromError:
        """Fetch and update user information and contracts.

        Returns:
            An OstromCustomerInfo object if the update was successful, or an OstromError if it failed.
        """

        # Fetch user information
        user: OstromUser | None = await self._fetch_user()

        if not user:
            return OstromError("Failed to fetch user information")

        contracts: list[OstromContract] | None = await self._fetch_contracts()

        if not contracts or len(contracts) == 0:
            return OstromError("Failed to fetch contracts")

        return OstromCustomerInfo(user=user, contracts=contracts)

    async def _fetch_user(self) -> OstromUser | None:
        """Fetch user information from Ostrom API."""
        user_data = await self.client.get_user()

        if not user_data:
            _LOGGER.warning("Failed to fetch user information from Ostrom API")
            return None

        user: OstromUser | None = OstromUser.parse(user_data)

        return user

    async def _fetch_contracts(self) -> list[OstromContract] | None:
        """Get list of all user contracts."""

        contract_data = await self.client.get_contracts()

        if not contract_data or "data" not in contract_data:
            _LOGGER.warning("Failed to fetch contracts from Ostrom API")
            return None

        contracts: list[OstromContract] = OstromContract.parse_list(contract_data)

        return contracts

    async def _fetch_energy_consumption(
        self, contract_id: str, time_start: datetime, time_end: datetime
    ) -> list[OstromConsumption] | None:
        """Fetch energy consumption data for a given contract ID."""

        consumption_data: (
            dict[str, list[dict[str, str | float]]] | None
        ) = await self.client.get_consumption_by_interval(
            start_date=time_start, end_date=time_end, contract_id=contract_id
        )

        if not consumption_data:
            _LOGGER.warning(
                "Failed to fetch energy consumption data for contract ID %s",
                contract_id,
            )
            return None

        consumption: list[OstromConsumption] | None = OstromConsumption.parse_list(
            consumption_data
        )

        return consumption

    async def _fetch_spot_prices(
        self, zip_code: str, time_start: datetime, time_end: datetime
    ) -> list[OstromSpotPrice] | None:
        """Fetch spot price data for a given zip code."""

        spot_price_data: (
            dict[str, list[dict[str, str | float]]] | None
        ) = await self.client.get_spot_prices_by_interval(
            start_date=time_start, end_date=time_end, zip_code=zip_code
        )

        if not spot_price_data:
            _LOGGER.warning("Failed to fetch spot price data for zip code %s", zip_code)
            return None

        spot_prices: list[OstromSpotPrice] | None = OstromSpotPrice.parse_list(
            spot_price_data
        )

        return spot_prices

    async def _fetch_data(self) -> OstromConsumerData | None:
        """Fetch and parse consumption and spot price data from the provider.

        Note on data availability for EPEX Spot:
         - Day-ahead prices: The order book closes around 12:00 CET/CEST, and results are published shortly after,
           typically from about 12:57 CET/CEST onward; preliminary can appear earlier
        - Intraday prices: Updated every 15 minutes, with a delay of about 5-10 minutes after the time slot starts
        - Most dynamic tariff integrations use the day-ahead auction result as the primary price source, which is only finalized after the noon auction.

        Returns:
            An OstromConsumerData object with the updated data.
        """

        if not self.contract_id or not self.zip_code:
            _LOGGER.warning("Contract ID or zip code not set, cannot fetch data")
            return None

        now = datetime.now(tz=UTC)

        # Currently live data is not available, the consumption from the past day can be accessed from noonish onwards.
        consumption_start_time: datetime = (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        consumption_time_end: datetime = consumption_start_time + timedelta(days=1)

        consumptions: (
            list[OstromConsumption] | None
        ) = await self._fetch_energy_consumption(
            self.contract_id, consumption_start_time, consumption_time_end
        )

        if consumptions is None:
            _LOGGER.warning("Failed to fetch consumption data")
            return None

        # Get spot price data for the same time range as consumption, plus future hours for forecasting
        tomorrow_start_time: datetime = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        spot_price_end_time: datetime = tomorrow_start_time + timedelta(days=1)

        spot_prices: list[OstromSpotPrice] | None = await self._fetch_spot_prices(
            self.zip_code, consumption_start_time, spot_price_end_time
        )

        if spot_prices is None:
            _LOGGER.warning("Failed to fetch spot price data")
            return None

        return OstromConsumerData.from_data(
            consumptions=consumptions, spot_prices=spot_prices
        )


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
