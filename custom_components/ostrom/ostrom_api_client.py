"""Ostrom electricity provider API Client.

Handles OAuth2 authentication and API requests for Ostrom API

Servers:
- Production:
  - https://auth.production.ostrom-api.io: Authentication and token management
  - https://production.ostrom-api.io: Access Ostrom API data
- Sandbox (not used in this integration):
  - https://auth.sandbox.ostrom-api.io: Authentication and token management
  - https://sandbox.ostrom-api.io: Access Ostrom API data

Endpoints:
- /oauth2/token: For obtaining access tokens
- /me: Get user/account information
- /contracts: Get list of user contracts
- /contracts/{contract_id}/energy-consumption: Get energy consumption data for a contract
- /spot-prices: Get spot price information for a zip code

"""

import asyncio
import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .ostrom_error import OstromError


class OstromAPIClient:
    """Client for interacting with the Ostrom API."""

    ENDPOINT_PRODUCTION_AUTH: str = "https://auth.production.ostrom-api.io"
    ENDPOINT_PRODUCTION_DATA: str = "https://production.ostrom-api.io"

    RESOURCE_OAUTH2_TOKEN: str = "/oauth2/token"
    RESOURCE_ME: str = "/me"
    RESOURCE_CONTRACTS: str = "/contracts"
    RESOURCE_ENERGY_CONSUMPTION: str = "/contracts/{contract_id}/energy-consumption"
    RESOURCE_SPOT_PRICES: str = "/spot-prices"
    REQUEST_TIMEOUT_SEC: int = 10
    TOKEN_EXPIRY_SKEW_SEC: int = 120

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        endpoint_auth: str | None = ENDPOINT_PRODUCTION_AUTH,
        endpoint_data: str | None = ENDPOINT_PRODUCTION_DATA,
    ) -> None:
        """Initialize the Ostrom API client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            endpoint_auth: OAuth2 authentication endpoint, default is production auth server
            endpoint_data: Base URL for API data endpoints, default is production data server
        """

        credentials: str = f"{client_id}:{client_secret}"

        endpoint_auth = (
            endpoint_auth
            if endpoint_auth is not None
            else OstromAPIClient.ENDPOINT_PRODUCTION_AUTH
        )

        endpoint_data = (
            endpoint_data
            if endpoint_data is not None
            else OstromAPIClient.ENDPOINT_PRODUCTION_DATA
        )

        self.credentials_b64: str = base64.b64encode(credentials.encode()).decode()

        self.api_base_url: str = endpoint_data
        self.auth_url: str = f"{endpoint_auth}{OstromAPIClient.RESOURCE_OAUTH2_TOKEN}"

        self.token: str | None = None
        self.expiry_time: datetime | None = None
        self._token_lock = asyncio.Lock()

    def _create_basic_auth(self) -> str:
        """Create Basic Authorization header from client credentials."""

        return f"Basic {self.credentials_b64}"

    async def refresh_access_token(self) -> OstromError | None:
        """Request a new valid access token.

        Returns:
            Access token string or None if unable to obtain
        """

        headers = {
            "accept": "application/json",
            "authorization": self._create_basic_auth(),
            "content-type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    self.auth_url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(
                        total=OstromAPIClient.REQUEST_TIMEOUT_SEC
                    ),
                ) as response,
            ):
                response.raise_for_status()
                token_response = await response.json()

                expires_in_sec = token_response.get("expires_in", 3600)

                self.expiry_time = datetime.now(tz=UTC) + timedelta(
                    seconds=expires_in_sec
                )

                self.token: str | None = token_response["access_token"]

        except aiohttp.ClientError as e:
            return OstromError(f"Failed to refresh access token: {e}", exception=e)
        else:
            return None

    async def get_access_token(self, force_refresh: bool = False) -> str | None:
        """Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: If True, forces a token refresh

        Returns:
            Access token string or None if unable to obtain
        """

        time_now: datetime = datetime.now(tz=UTC)

        # Check if a token exists and is still valid with a safety margin.
        # This prevents edge cases where the token expires between validation and request.
        token_valid_with_skew: bool = (
            self.token is not None
            and self.expiry_time is not None
            and (time_now + timedelta(seconds=OstromAPIClient.TOKEN_EXPIRY_SKEW_SEC))
            < self.expiry_time
        )

        if token_valid_with_skew and not force_refresh:
            return self.token

        # Serialize refreshes to avoid race conditions across concurrent requests.
        async with self._token_lock:
            time_now = datetime.now(tz=UTC)

            token_valid_with_skew = (
                self.token is not None
                and self.expiry_time is not None
                and (
                    time_now + timedelta(seconds=OstromAPIClient.TOKEN_EXPIRY_SKEW_SEC)
                )
                < self.expiry_time
            )

            if token_valid_with_skew and not force_refresh:
                return self.token

            current_token = self.token
            current_expiry = self.expiry_time

            refresh_error = await self.refresh_access_token()

            if refresh_error is not None:
                # Fallback to currently cached token if still valid at this moment.
                if (
                    current_token is not None
                    and current_expiry is not None
                    and datetime.now(tz=UTC) < current_expiry
                ):
                    return current_token

                self.token = None
                self.expiry_time = None
                return None

            return self.token

    async def make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | None:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (e.g., '/me', '/contracts')
            **kwargs: Additional arguments to pass to aiohttp

        Returns:
            JSON response as dict or None if request fails
        """
        # Ensure we have a valid token
        token = await self.get_access_token()

        if token is None:
            return None

        # Build full URL
        url = f"{self.api_base_url}{endpoint}"

        # Add authorization header
        headers = kwargs.pop("headers", {})
        headers["authorization"] = f"Bearer {token}"
        headers.setdefault("accept", "application/json")

        # Add timeout
        timeout = aiohttp.ClientTimeout(total=OstromAPIClient.REQUEST_TIMEOUT_SEC)

        # Make request
        async with (
            aiohttp.ClientSession() as session,
            session.request(
                method, url, headers=headers, timeout=timeout, **kwargs
            ) as response,
        ):
            # If unauthorized, try refreshing token once
            if response.status == 401:
                self.token = None
                self.expiry_time = None

                token = await self.get_access_token(force_refresh=True)

                if token is None:
                    return None

                headers["authorization"] = f"Bearer {token}"

                async with session.request(
                    method, url, headers=headers, timeout=timeout, **kwargs
                ) as retry_response:
                    retry_response.raise_for_status()
                    return await retry_response.json()

            response.raise_for_status()
            return await response.json()

    async def get_user(self) -> dict[str, str] | None:
        """Get current user/account information.

        Example response:

        ```json
        {
            "email": "<user_email>",
            "firstName": "<user_first_name>",
            "lastName": "<user_last_name>",
            "language": "<user_language>"
        }
        ```

        Returns:
            User information as a dictionary.

        """
        return await self.make_request("GET", OstromAPIClient.RESOURCE_ME)

    async def get_contracts(self) -> dict[str, Any] | None:
        """Get list of contracts.

        Example response:

        ```json
        {
            "data": [
                {
                    "id": 123456789,
                    "type": "ELECTRICITY",
                    "productCode": "SIMPLY_DYNAMIC",
                    "status": "ACTIVE",
                    "customerFirstName": "FirstName",
                    "customerLastName": "LastName",
                    "startDate": "2020-01-01",
                    "currentMonthlyDepositAmount": 0,
                    "address": {
                        "zip": "12345",
                        "city": "CityName",
                        "street": "StreetName",
                        "houseNumber": "123"
                    }
                }
            ]
        }
        ```

        """
        return await self.make_request("GET", OstromAPIClient.RESOURCE_CONTRACTS)

    async def get_consumption_by_interval(
        self,
        contract_id: str,
        start_date: datetime,
        end_date: datetime,
        resolution: str = "HOUR",
    ) -> dict[str, list[dict[str, str | float]]] | None:
        """Get energy consumption data within a time frame with the specified resolution for a contract.

        Example response:

        ```json
        {
            "data": [
                {
                    "date": "1970-01-01T00:00:00.000Z",
                    "kWh": 0.317
                },
                {
                    "date": "1970-01-01T01:00:00.000Z",
                    "kWh": 0.256
                }
            ]
        }
        ```

        Args:
            contract_id: ID of the contract
            start_date: Start date as datetime object
            end_date: End date as datetime object
            resolution: Data resolution ('HOUR', 'DAY', 'MONTH'), default is 'HOUR'

        Returns:
            Consumption data with date time in iso format and the consumption in kWh per interval as a dictionary.
        """

        endpoint = OstromAPIClient.RESOURCE_ENERGY_CONSUMPTION.format(
            contract_id=contract_id
        )

        start: datetime = start_date.replace(minute=0, second=0, microsecond=0)
        end: datetime = end_date.replace(minute=0, second=0, microsecond=0)

        params: dict[str, str] = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "resolution": resolution,
        }

        return await self.make_request("GET", endpoint, params=params)

    async def get_spot_prices_by_interval(
        self,
        start_date: datetime,
        end_date: datetime,
        zip_code: str,
        resolution: str = "HOUR",
    ) -> dict[str, list[dict[str, str | float]]] | None:
        """Get spot prices within a time frame with the specified resolution for a given zip code.

        Example response:

        ```json
        "data": [
        {
            "date": "1970-01-01T00:00:00.000Z",
            "netMwhPrice": 92.79,
            "netKwhPrice": 9.28,
            "grossKwhPrice": 11.05,
            "netKwhTaxAndLevies": 14.94,
            "grossKwhTaxAndLevies": 17.78,
            "netMonthlyOstromBaseFee": 5.05,
            "grossMonthlyOstromBaseFee": 6,
            "netMonthlyGridFees": 9.35,
            "grossMonthlyGridFees": 11.12
        },
        ]
        ```

        Args:
            start_date: Start date as datetime object
            end_date: End date as datetime object
            zip_code: Zip code
            resolution: Data resolution ('HOUR', 'DAY', 'MONTH'), default is 'HOUR'

        Returns:
            Spot price data with date time in iso format and the spot price in EUR per kWh per interval as a dictionary.
        """

        endpoint = OstromAPIClient.RESOURCE_SPOT_PRICES
        start: datetime = start_date.replace(minute=0, second=0, microsecond=0)
        end: datetime = end_date.replace(minute=0, second=0, microsecond=0)

        params: dict[str, str] = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "zip": zip_code,
            "resolution": resolution,
        }

        return await self.make_request("GET", endpoint, params=params)
