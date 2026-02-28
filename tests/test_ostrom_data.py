"""Tests for Ostrom data helper logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.ostrom.ostrom_data import OstromConsumerData, OstromSpotPrice


def _spot_price_at(ts: datetime, total_price: float) -> OstromSpotPrice:
    """Create a spot-price entry with a given total gross price in EUR/kWh."""
    return OstromSpotPrice(
        date=ts,
        price_net_euro_per_mwh=0.0,
        price_net_euro_per_kwh=0.0,
        price_gross_euro_per_kwh=total_price,
        tax_and_levies_net_euro_per_kwh=0.0,
        tax_and_levies_gross_euro_per_kwh=0.0,
        base_fee_net_euro_per_month=0.0,
        base_fee_gross_euro_per_month=0.0,
        grid_fees_net_euro_per_month=0.0,
        grid_fees_gross_euro_per_month=0.0,
    )


def test_time_range_end_is_exclusive_for_minimum_lookup() -> None:
    """End boundary must be exclusive to avoid spilling into next day."""
    day_start = datetime(2026, 2, 21, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    last_hour_today = _spot_price_at(day_end - timedelta(hours=1), total_price=0.30)
    first_hour_next_day = _spot_price_at(day_end, total_price=0.10)

    result = OstromConsumerData.find_minimum_spot_price_time_range(
        [last_hour_today, first_hour_next_day],
        day_start,
        day_end,
    )

    assert result is last_hour_today
