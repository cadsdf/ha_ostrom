"""Tests for Ostrom config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ostrom.const import DOMAIN, KEY_CONTRACT_ID, KEY_PASSWORD, KEY_USER
from custom_components.ostrom.ostrom_error import OstromError


async def test_config_flow_user_and_select_contract(hass, sample_contract) -> None:
    """Config flow should proceed from user creds to contract selection and entry creation."""
    with patch("custom_components.ostrom.config_flow.OstromProvider") as provider_cls:
        provider = provider_cls.return_value
        provider.initialize = AsyncMock(return_value=None)
        provider.get_contracts.return_value = [sample_contract]

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={KEY_USER: "user@example.com", KEY_PASSWORD: "secret"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "select_contract"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"contract": sample_contract.id},
        )

        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert result2["data"][KEY_CONTRACT_ID] == sample_contract.id


async def test_config_flow_no_contracts_error(hass) -> None:
    """Config flow should report no_contracts when account has none."""
    with patch("custom_components.ostrom.config_flow.OstromProvider") as provider_cls:
        provider = provider_cls.return_value
        provider.initialize = AsyncMock(return_value=None)
        provider.get_contracts.return_value = []

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={KEY_USER: "user@example.com", KEY_PASSWORD: "secret"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "no_contracts"


async def test_config_flow_rate_limited_error(hass) -> None:
    """Config flow should report rate_limited on HTTP 429."""
    with patch("custom_components.ostrom.config_flow.OstromProvider") as provider_cls:
        provider = provider_cls.return_value
        provider.initialize = AsyncMock(
            return_value=OstromError(
                "Failed to refresh access token",
                exception=aiohttp.ClientResponseError(
                    request_info=None,
                    history=(),
                    status=429,
                    message="Too Many Requests",
                ),
            )
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={KEY_USER: "user@example.com", KEY_PASSWORD: "secret"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "rate_limited"
