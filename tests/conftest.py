"""Shared test fixtures for Ostrom integration."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.ostrom.const import (
    DOMAIN,
    KEY_ADDRESS,
    KEY_CONTRACT_ID,
    KEY_PASSWORD,
    KEY_USER,
    KEY_ZIP_CODE,
)
from custom_components.ostrom.ostrom_data import (
    OstromConsumerData,
    OstromContract,
    OstromSpotPrice,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def sample_contract() -> OstromContract:
    """Create a representative contract."""
    return OstromContract(
        id="1234",
        type="ELECTRICITY",
        product_code="SIMPLY_DYNAMIC",
        status="ACTIVE",
        customer_first_name="Max",
        customer_last_name="Mustermann",
        start_date=datetime(2024, 1, 1),
        current_monthly_deposit_amount=0.0,
        address_zip="10115",
        address_city="Berlin",
        address_street="Teststrasse",
        address_house_number="1",
    )


@pytest.fixture
def sample_spot_price() -> OstromSpotPrice:
    """Create a representative spot-price record."""
    return OstromSpotPrice(
        date=datetime.now(tz=UTC),
        price_net_euro_per_mwh=92.79,
        price_net_euro_per_kwh=0.09279,
        price_gross_euro_per_kwh=0.1105,
        tax_and_levies_net_euro_per_kwh=0.1494,
        tax_and_levies_gross_euro_per_kwh=0.1778,
        base_fee_net_euro_per_month=5.05,
        base_fee_gross_euro_per_month=6.0,
        grid_fees_net_euro_per_month=9.35,
        grid_fees_gross_euro_per_month=11.12,
    )


@pytest.fixture
def sample_consumer_data(sample_spot_price: OstromSpotPrice) -> OstromConsumerData:
    """Create a representative consumer-data object."""
    return OstromConsumerData(
        ok=True,
        error=None,
        timestamp=sample_spot_price.date,
        spot_price_now=sample_spot_price,
        spot_price_minimum_today=sample_spot_price,
        spot_price_minimum_remaining_today=sample_spot_price,
        spot_price_minimum_tomorrow=sample_spot_price,
        spot_price_minimum_all_available=sample_spot_price,
        minimum_is_current_price=True,
        spot_prices=[sample_spot_price],
        consumptions=[],
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a config entry for Ostrom integration tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Ostrom Test",
        data={
            KEY_USER: "user@example.com",
            KEY_PASSWORD: "secret",
            KEY_CONTRACT_ID: "1234",
            KEY_ZIP_CODE: "10115",
            KEY_ADDRESS: "Berlin, Teststrasse 1 (10115)",
        },
    )
