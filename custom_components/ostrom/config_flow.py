"""Config flow for Ostrom integration."""

from __future__ import annotations

import logging
from typing import Any, NoReturn

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)

from .const import (
    DOMAIN,
    KEY_ADDRESS,
    KEY_CONTRACT_ID,
    KEY_PASSWORD,
    KEY_USER,
    KEY_ZIP_CODE,
)
from .ostrom_data import OstromContract
from .ostrom_error import OstromError
from .ostrom_provider import OstromProvider

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(KEY_USER): str,
        vol.Required(KEY_PASSWORD): str,
    }
)


def _format_contract_label(contract: OstromContract) -> str:
    """Format a contract display string for selection list."""
    return (
        f"{contract.address_city}, "
        f"{contract.address_street} {contract.address_house_number} "
        f"({contract.address_zip}) [{contract.id}]"
    )


def _raise_invalid_auth() -> NoReturn:
    """Raise an auth failure exception."""
    raise ConfigEntryAuthFailed


def _raise_cannot_connect() -> NoReturn:
    """Raise a connection failure exception."""
    raise ConfigEntryNotReady


def _raise_no_contracts_found() -> NoReturn:
    """Raise a missing contracts exception."""
    raise NoContractsFound


def _raise_initialize_error(error: OstromError) -> NoReturn:
    """Map provider initialization errors to Home Assistant exceptions."""
    if (
        isinstance(error.exception, aiohttp.ClientResponseError)
        and error.exception.status == 401
    ):
        _raise_invalid_auth()

    _raise_cannot_connect()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Ostrom config flow."""

    # required for config flow versioning
    VERSION = 7

    def __init__(self) -> None:
        """Initialize flow state."""
        self.user: str | None = None
        self.password: str | None = None
        self.provider: OstromProvider | None = None
        self.contracts_by_id: dict[str, OstromContract] = {}
        self.contract_choices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[KEY_USER]
            self.password = user_input[KEY_PASSWORD]

            self.provider = OstromProvider(
                user=self.user,
                password=self.password,
            )

            try:
                error: OstromError | None = await self.provider.initialize()
                if error is not None:
                    _raise_initialize_error(error)

                contracts = self.provider.get_contracts()
                if not contracts:
                    _raise_no_contracts_found()

                self.contracts_by_id = {contract.id: contract for contract in contracts}
                self.contract_choices = {
                    contract.id: _format_contract_label(contract)
                    for contract in contracts
                }

                return await self.async_step_select_contract()

            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
                _LOGGER.warning("Invalid authentication for user %s", self.user)
            except ConfigEntryNotReady:
                errors["base"] = "cannot_connect"
                _LOGGER.warning("Cannot connect for user %s", self.user)
            except NoContractsFound:
                errors["base"] = "no_contracts"
                _LOGGER.warning("No contracts found for user %s", self.user)
            except Exception:
                errors["base"] = "unknown"
                _LOGGER.exception("Unexpected exception during Ostrom config flow")

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle contract selection step."""
        contract_schema = vol.Schema(
            {vol.Required(KEY_CONTRACT_ID): vol.In(self.contract_choices)}
        )

        errors: dict[str, str] = {}

        if user_input is not None:
            contract_id: str = user_input[KEY_CONTRACT_ID]

            await self.async_set_unique_id(contract_id)
            self._abort_if_unique_id_configured()

            selected_contract = self.contracts_by_id.get(contract_id)
            if selected_contract is None:
                errors["base"] = "unknown"
            else:
                address = (
                    f"{selected_contract.address_city}, "
                    f"{selected_contract.address_street} "
                    f"{selected_contract.address_house_number} "
                    f"({selected_contract.address_zip})"
                )

                entry_data: dict[str, Any] = {
                    KEY_USER: self.user,
                    KEY_PASSWORD: self.password,
                    KEY_CONTRACT_ID: contract_id,
                    KEY_ZIP_CODE: selected_contract.address_zip,
                    KEY_ADDRESS: address,
                }

                return self.async_create_entry(
                    title=f"Ostrom {address}",
                    data=entry_data,
                )

        return self.async_show_form(
            step_id="select_contract",
            data_schema=contract_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        _: config_entries.ConfigEntry,
    ) -> OstromOptionsFlowHandler:
        """Get options flow handler."""
        return OstromOptionsFlowHandler()


class OstromOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    async def async_step_init(self, user_input=None) -> dict[str, Any]:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )


class NoContractsFound(HomeAssistantError):
    """Error to indicate no contracts are available for this account."""
