"""Ostrom Energy Data Parser.

Parse raw data received from Ostrom API, check for integrity, and map to common data structure
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any, TypeVar

T = TypeVar("T", "OstromSpotPrice", "OstromConsumption")


@dataclass
class OstromUser:
    """Data structure for user information."""

    email: str
    first_name: str
    last_name: str
    language: str

    @classmethod
    def parse(cls, data: dict[str, str]) -> OstromUser | None:
        """Create OstromUser from API response dictionary.

        Expected input format (example):

        ```
        {
            "email": "<user_email>",
            "firstName": "<user_first_name>",
            "lastName": "<user_last_name>",
            "language": "<user_language>"
        }
        ```

        This method parses the raw data received from the Ostrom API, checks for the presence of required fields,
        and maps the values to the OstromUser data structure. If any required fields are missing or if
        the input data is not in the expected format, it returns None.
        """

        try:
            result = cls(
                email=str(data["email"]),
                first_name=str(data["firstName"]),
                last_name=str(data["lastName"]),
                language=str(data["language"]),
            )

        except (KeyError, ValueError, TypeError):
            return None
        else:
            return result


@dataclass
class OstromContract:
    """Data structure for contract information."""

    id: str
    type: str
    product_code: str
    status: str
    customer_first_name: str
    customer_last_name: str
    start_date: datetime
    current_monthly_deposit_amount: float
    address_zip: str
    address_city: str
    address_street: str
    address_house_number: str

    @classmethod
    def parse(cls, data: dict[str, Any]) -> OstromContract | None:
        """Create OstromContract from API response dictionary.

        Parse the raw data received from the Ostrom API for contract information, check for the presence of required fields,
        and map the values to the OstromContract data structure. If any required fields are missing or if
        the input data is not in the expected format, it returns None.

        Expected input format (example):

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

        Args:
            data: The raw response from the Ostrom API for contract information.

        Returns:
            An OstromContract object containing the contract ID and name, or None if the input data
        """

        try:
            result = cls(
                id=str(data["id"]),
                type=str(data["type"]),
                product_code=str(data["productCode"]),
                status=str(data["status"]),
                customer_first_name=str(data["customerFirstName"]),
                customer_last_name=str(data["customerLastName"]),
                start_date=datetime.fromisoformat(str(data["startDate"])),
                current_monthly_deposit_amount=float(
                    data["currentMonthlyDepositAmount"]
                ),
                address_zip=str(data["address"]["zip"]),
                address_city=str(data["address"]["city"]),
                address_street=str(data["address"]["street"]),
                address_house_number=str(data["address"]["houseNumber"]),
            )

        except (KeyError, ValueError, TypeError):
            return None
        else:
            return result

    @classmethod
    def parse_list(cls, data: dict[str, list[dict[str, Any]]]) -> list[OstromContract]:
        """Parse a server contract response into a list of OstromContract objects.

        This method takes the raw response from the Ostrom API, which is expected to be a dictionary
        containing a "data" key with a list of contract entries.
        Each entry is parsed using the parse method to create an OstromContract object.

        Expected input format (example):

        ```json
        {
            "data": [
            {
                "id": 123456789,
                ...
            },
            {
                "id": 987654321,
                ...
            }
            ]
        }
        ```

        Args:
            data: The raw response from the Ostrom API for contract information.

        Returns:
            A list of OstromContract objects parsed from the input data.
        """

        contracts: list[OstromContract] = []

        if "data" not in data:
            return contracts

        for entry in data["data"]:
            contract = cls.parse(entry)

            if contract:
                contracts.append(contract)

        return contracts


@dataclass
class OstromCustomerInfo:
    """Data structure for user and contract information."""

    user: OstromUser
    contracts: list[OstromContract]


@dataclass
class OstromSpotPrice:
    """Data structure for energy price information."""

    date: datetime
    price_net_euro_per_mwh: float
    price_net_euro_per_kwh: float
    price_gross_euro_per_kwh: float
    tax_and_levies_net_euro_per_kwh: float
    tax_and_levies_gross_euro_per_kwh: float
    base_fee_net_euro_per_month: float
    base_fee_gross_euro_per_month: float
    grid_fees_net_euro_per_month: float
    grid_fees_gross_euro_per_month: float

    @classmethod
    def parse(cls, data: dict[str, str | float]) -> OstromSpotPrice | None:
        """Create OstromSpotPrice from API response dictionary.

        Expected input format (example):

        ```
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
        }
        ```

        This method parses the raw data received from the Ostrom API, checks for the presence of required fields,
        and maps the values to the OstromSpotPrice data structure. It also converts date strings to datetime objects and ensures that all price values are floats. If any required fields are missing or if
        """

        try:
            result = cls(
                date=datetime.fromisoformat(str(data["date"])),
                price_net_euro_per_mwh=float(data["netMwhPrice"]),
                price_net_euro_per_kwh=float(data["netKwhPrice"]) / 100.0,
                price_gross_euro_per_kwh=float(data["grossKwhPrice"]) / 100.0,
                tax_and_levies_net_euro_per_kwh=float(data["netKwhTaxAndLevies"])
                / 100.0,
                tax_and_levies_gross_euro_per_kwh=float(data["grossKwhTaxAndLevies"])
                / 100.0,
                base_fee_net_euro_per_month=float(data["netMonthlyOstromBaseFee"]),
                base_fee_gross_euro_per_month=float(data["grossMonthlyOstromBaseFee"]),
                grid_fees_net_euro_per_month=float(data["netMonthlyGridFees"]),
                grid_fees_gross_euro_per_month=float(data["grossMonthlyGridFees"]),
            )

        except (KeyError, ValueError, TypeError):
            return None
        else:
            return result

    @classmethod
    def parse_list(
        cls, data: dict[str, list[dict[str, str | float]]]
    ) -> list[OstromSpotPrice]:
        """Parse a server spot price response into a list of OstromSpotPrice objects.

        This method takes the raw response from the Ostrom API, which is expected to be a dictionary
        containing a "data" key with a list of spot price entries.
        Each entry is parsed using the parse method to create an OstromSpotPrice object.

        Expected input format (example):

        ```
        {
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
                {
                    "date": "1970-01-01T01:00:00.000Z",
                    "netMwhPrice": 92.96,
                    "netKwhPrice": 9.3,
                    "grossKwhPrice": 11.07,
                    "netKwhTaxAndLevies": 14.94,
                    "grossKwhTaxAndLevies": 17.78,
                    "netMonthlyOstromBaseFee": 5.05,
                    "grossMonthlyOstromBaseFee": 6,
                    "netMonthlyGridFees": 9.35,
                    "grossMonthlyGridFees": 11.12
                }
            ]
        }
        ```

        Args:
            data: The raw response from the Ostrom API.

        Returns:
            A list of OstromSpotPrice objects parsed from the input data.
        """

        spot_prices: list[OstromSpotPrice] = []

        if "data" not in data:
            return spot_prices

        for entry in data["data"]:
            spot_price = cls.parse(entry)

            if spot_price:
                spot_prices.append(spot_price)

        return spot_prices


@dataclass
class OstromConsumption:
    """Data structure for energy consumption information."""

    date: datetime
    consumption_kwh: float

    @classmethod
    def parse(cls, data: dict[str, str | float]) -> OstromConsumption | None:
        """Create OstromConsumption from API response dictionary.

        Expected input format (example):

        ```
        {
            "date": "1970-01-01T00:00:00.000Z",
            "consumptionKwh": 1.5
        }
        ```

        This method parses the raw data received from the Ostrom API, checks for the presence of required fields,
        and maps the values to the OstromConsumption data structure. It also converts date strings to datetime objects and ensures that consumption values are floats. If any required fields are missing or if
        """

        try:
            result = cls(
                date=datetime.fromisoformat(str(data["date"])),
                consumption_kwh=float(data["kWh"]),
            )

        except (KeyError, ValueError, TypeError):
            return None
        else:
            return result

    @classmethod
    def parse_list(
        cls, data: dict[str, list[dict[str, str | float]]]
    ) -> list[OstromConsumption]:
        """Parse a server consumption response into a list of OstromConsumption objects.

        This method takes the raw response from the Ostrom API, which is expected to be a dictionary
        containing a "data" key with a list of consumption entries.
        Each entry is parsed using the parse method to create an OstromConsumption object.

        Expected input format (example):

        ```
        {
            "data": [
                {
                    "date": "1970-01-01T00:00:00.000Z",
                    "consumptionKwh": 1.5
                },
                {
                    "date": "1970-01-01T01:00:00.000Z",
                    "consumptionKwh": 1.7
                }
            ]
        }
        ```
        Args:
            data: The raw response from the Ostrom API.

        Returns:
            A list of OstromConsumption objects parsed from the input data.
        """

        consumptions: list[OstromConsumption] = []

        if "data" not in data:
            return consumptions

        for entry in data["data"]:
            consumption = cls.parse(entry)

            if consumption:
                consumptions.append(consumption)

        return consumptions


@dataclass
class OstromAggregatedData:
    """Data structure for combined energy price and consumption information."""

    spot_prices: list[OstromSpotPrice]
    consumption: list[OstromConsumption]

    @classmethod
    def parse(
        cls,
        spot_price_data: dict[str, list[dict[str, str | float]]],
        consumption_data: dict[str, list[dict[str, str | float]]],
    ) -> OstromAggregatedData | None:
        """Parse raw spot price and consumption data into an OstromAggregatedData object.

        This method takes the raw responses from the Ostrom API for both spot prices and consumption,
        parses them using the respective parse_list methods of OstromSpotPrice and OstromConsumption,
        and combines the results into a single OstromAggregatedData object.

        Args:
            spot_price_data: The raw response from the Ostrom API for spot prices.
            consumption_data: The raw response from the Ostrom API for consumption.

        Returns:
            An OstromAggregatedData object containing lists of parsed spot prices and consumption data.
        """

        spot_prices = OstromSpotPrice.parse_list(spot_price_data)

        if not spot_prices:
            return None

        consumption = OstromConsumption.parse_list(consumption_data)

        if not consumption:
            return None

        return cls(spot_prices=spot_prices, consumption=consumption)


@dataclass
class OstromConsumerData:
    """Data structure for combined energy price and consumption information."""

    ok: bool = False
    error: str | None = None
    timestamp: datetime | None = None

    spot_price_now: OstromSpotPrice | None = None
    spot_price_minimum_today: OstromSpotPrice | None = None
    spot_price_minimum_remaining_today: OstromSpotPrice | None = None
    spot_price_minimum_tomorrow: OstromSpotPrice | None = None
    spot_price_minimum_all_available: OstromSpotPrice | None = None

    minimum_is_current_price: bool = False

    spot_prices: list[OstromSpotPrice] | None = None
    consumptions: list[OstromConsumption] | None = None

    @classmethod
    def parse(
        cls,
        spot_price_data: dict[str, list[dict[str, str | float]]],
        consumption_data: dict[str, list[dict[str, str | float]]],
    ) -> OstromConsumerData | None:
        """Parse raw spot price and consumption data into an OstromConsumerData object.

        This method takes the raw responses from the Ostrom API for both spot prices and consumption,
        parses them using the respective parse_list methods of OstromSpotPrice and OstromConsumption,
        and combines the first spot price (current) and the last consumption entry into a single OstromConsumerData object.

        Args:
            spot_price_data: The raw response from the Ostrom API for spot prices.
            consumption_data: The raw response from the Ostrom API for consumption.

        Returns:
            An OstromConsumerData object containing the current spot price and the last consumption data.
        """
        spot_prices = OstromSpotPrice.parse_list(spot_price_data)

        if not spot_prices:
            return None

        consumptions = OstromConsumption.parse_list(consumption_data)

        if not consumptions:
            return None

        return cls.from_data(consumptions, spot_prices)

    @classmethod
    def from_data(
        cls,
        consumptions: list[OstromConsumption],
        spot_prices: list[OstromSpotPrice],
        time_zone: tzinfo = UTC,
    ) -> OstromConsumerData | None:
        """Build consumer data from parsed consumption and spot price lists."""
        spot_price: OstromSpotPrice | None = cls.find_current_item(spot_prices)

        if not spot_price:
            return None

        minimum_spot_price_today: OstromSpotPrice | None = (
            OstromConsumerData.find_minimum_spot_price_current_day(
                spot_prices, time_zone=time_zone
            )
        )

        minimum_spot_price_today_from_now: OstromSpotPrice | None = (
            OstromConsumerData.find_minimum_spot_price_current_day_from_now(
                spot_prices, time_zone=time_zone
            )
        )

        minimum_spot_price_tomorrow: OstromSpotPrice | None = (
            OstromConsumerData.find_minimum_spot_price_tomorrow(
                spot_prices, time_zone=time_zone
            )
        )

        minimum_spot_price_all_available: OstromSpotPrice | None = (
            OstromConsumerData.find_minimum_spot_price_all_available(spot_prices)
        )

        minimums_available: bool = minimum_spot_price_today_from_now is not None

        minimum_is_current_price: bool = (
            minimums_available and spot_price == minimum_spot_price_today_from_now
        )

        return cls(
            timestamp=spot_price.date,
            spot_price_now=spot_price,
            spot_price_minimum_today=minimum_spot_price_today,
            spot_price_minimum_remaining_today=minimum_spot_price_today_from_now,
            spot_price_minimum_tomorrow=minimum_spot_price_tomorrow,
            spot_price_minimum_all_available=minimum_spot_price_all_available,
            minimum_is_current_price=minimum_is_current_price,
            spot_prices=spot_prices,
            consumptions=consumptions,
        )

    @staticmethod
    def find_closest_item_by_time(data: Sequence[T], target_time: datetime) -> T | None:
        """Find the item with the closest timestamp to the target datetime."""
        diff_min_sec: float | None = None
        item_min: T | None = None

        for item in data:
            diff_new_sec = abs((item.date - target_time).total_seconds())
            if diff_min_sec is None or diff_new_sec < diff_min_sec:
                diff_min_sec = diff_new_sec
                item_min = item

        return item_min

    @staticmethod
    def gross_price_with_tax_euro_per_kwh(spot_price: OstromSpotPrice) -> float:
        """Calculate the gross price with tax in euros per kWh for a given spot price entry.

        Args:
            spot_price: An OstromSpotPrice object containing the price and tax information.

        Returns:
            The gross price with tax in euros per kWh calculated from the spot price entry.
        """

        return (
            spot_price.price_gross_euro_per_kwh
            + spot_price.tax_and_levies_gross_euro_per_kwh
        )

    @staticmethod
    def find_index_data_time_now(
        data: Sequence[T],
    ) -> int | None:
        """Find the index of the spot price or consumption entry that corresponds to the current time.

        Args:
            data: A list of OstromSpotPrice or OstromConsumption objects to search through.

        Returns:
            The index of the spot price or consumption entry that matches the current time, or None if not found.
        """

        now: datetime = datetime.now(tz=UTC)
        diff_min_sec: float | None = None
        index_min: int | None = None

        for index, item in enumerate(data):
            diff_new_sec = abs((item.date - now).total_seconds())

            if diff_min_sec is None or diff_new_sec < diff_min_sec:
                diff_min_sec = diff_new_sec
                index_min = index

        return index_min

    @staticmethod
    def find_current_item(data: Sequence[T]) -> T | None:
        """Find the spot price or consumption entry that corresponds to the current time.

        Args:
            data: A list of OstromSpotPrice or OstromConsumption objects to search through.

        Returns:
            The spot price or consumption entry that matches the current time, or None if not found.

        """
        index = OstromConsumerData.find_index_data_time_now(data)

        if index is not None and index >= 0 and index < len(data):
            return data[index]

        return None

    @staticmethod
    def find_minimum_spot_price_time_range(
        data: Sequence[OstromSpotPrice], time_start: datetime, time_end: datetime
    ) -> OstromSpotPrice | None:
        """Find the spot price entry with the lowest gross price within a specified time range.

        Args:
            data: A list of OstromSpotPrice objects to search through.
            time_start: The start of the time range to consider.
            time_end: The end of the time range to consider.

        Returns:
            The spot price entry with the lowest gross price within the specified time range, or None if not found.

        Notes:
            `time_end` is treated as exclusive, i.e. the checked interval is [time_start, time_end).
        """
        min_price: float | None = None
        min_price_entry: OstromSpotPrice | None = None

        for entry in data:
            if entry.date < time_start or entry.date >= time_end:
                continue

            price_with_tax_gross_euro_per_kwh: float = (
                OstromConsumerData.gross_price_with_tax_euro_per_kwh(entry)
            )

            if min_price is None or price_with_tax_gross_euro_per_kwh < min_price:
                min_price = price_with_tax_gross_euro_per_kwh
                min_price_entry = entry

        return min_price_entry

    @staticmethod
    def find_minimum_spot_price_next_hours(
        data: Sequence[OstromSpotPrice], hours_ahead: int
    ) -> OstromSpotPrice | None:
        """Find the spot price entry with the lowest gross price within the next specified hours.

        Args:
            data: A list of OstromSpotPrice objects to search through.
            hours_ahead: The number of hours ahead to consider for finding the minimum spot price.

        Returns:
            The spot price entry with the lowest gross price within the next specified hours, or None if not found.
        """
        now = datetime.now(tz=UTC)
        time_end = now + timedelta(hours=hours_ahead)

        return OstromConsumerData.find_minimum_spot_price_time_range(
            data, now, time_end
        )

    @staticmethod
    def find_minimum_spot_price_current_day(
        data: Sequence[OstromSpotPrice],
        time_zone: tzinfo = UTC,
    ) -> OstromSpotPrice | None:
        """Find the spot price entry with the lowest gross price for the current day.

        Args:
            data: A list of OstromSpotPrice objects to search through.

        Returns:
            The spot price entry with the lowest gross price for the current day, or None if not found.
        """

        now = datetime.now(tz=time_zone)
        time_start = datetime(now.year, now.month, now.day, tzinfo=time_zone)
        time_end = time_start + timedelta(days=1)

        return OstromConsumerData.find_minimum_spot_price_time_range(
            data, time_start, time_end
        )

    @staticmethod
    def find_minimum_spot_price_current_day_from_now(
        data: Sequence[OstromSpotPrice],
        time_zone: tzinfo = UTC,
    ) -> OstromSpotPrice | None:
        """Find the spot price entry with the lowest gross price for the current day starting from now.

        Args:
            data: A list of OstromSpotPrice objects to search through.

        Returns:
            The spot price entry with the lowest gross price for the current day starting from now, or None if not found.
        """

        now = datetime.now(tz=time_zone)
        time_start = now

        time_end = datetime(now.year, now.month, now.day, tzinfo=time_zone) + timedelta(
            days=1
        )

        return OstromConsumerData.find_minimum_spot_price_time_range(
            data, time_start, time_end
        )

    @staticmethod
    def find_minimum_spot_price_tomorrow(
        data: Sequence[OstromSpotPrice],
        time_zone: tzinfo = UTC,
    ) -> OstromSpotPrice | None:
        """Find the minimum spot price for tomorrow."""
        now = datetime.now(tz=time_zone)

        tomorrow_start = datetime(
            now.year, now.month, now.day, tzinfo=time_zone
        ) + timedelta(days=1)

        tomorrow_end = tomorrow_start + timedelta(days=1)

        return OstromConsumerData.find_minimum_spot_price_time_range(
            data, tomorrow_start, tomorrow_end
        )

    @staticmethod
    def find_minimum_spot_price_all_available(
        data: Sequence[OstromSpotPrice],
    ) -> OstromSpotPrice | None:
        """Find the minimum spot price across all available entries."""
        min_price_entry: OstromSpotPrice | None = None
        min_price: float | None = None

        for entry in data:
            price = OstromConsumerData.gross_price_with_tax_euro_per_kwh(entry)

            if min_price is None or price < min_price:
                min_price = price
                min_price_entry = entry

        return min_price_entry
