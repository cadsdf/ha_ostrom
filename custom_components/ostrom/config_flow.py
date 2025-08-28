""" ConfigFlow for Ostrom """

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

#import requests
from .ostrom_api import OstromApi, APIAuthError, APIConnectionError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("apiuser"): str,
        vol.Required("apipass"): str,
    })
    
# Add your boolean option key here
OPTION_BOOL_KEY = "use_past_sensor"

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(OPTION_BOOL_KEY, default=False): bool,
    }
)
    

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
   
    """Validate the user input allows us to connect.
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    
    api = OstromApi(data["apiuser"], data["apipass"])
    
    try:
        # TODO: Change this to use a real api call for data
        await hass.async_add_executor_job(api.ostrom_outh)
        # If the authentication is wrong, raise InvalidAuth
    except APIAuthError as err:
        _LOGGER.error("Auth Error {0} ",err)
        raise InvalidAuth from err
    return {"title": f"Example Integration - {data[apiuser]}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Ostrom config flow with selectable single contract and consumption option."""

    VERSION = 6
    
    def __init__(self):
        self.api = None
        self.contract_choices = {}
        self.contracts = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle inital step."""
        errors = {}
        if user_input is not None:
            # lege die Api an
            self.api = OstromApi(data["apiuser"], data["apipass"])
            try:
                # test zugangsdaten
                await hass.async_add_executor_job(api.ostrom_outh)   
                # alle verträge holen
                contracts = await self.hass.async_add_executor_job(api.ostrom_contracts)
                contract_choices = {}
                for vertrag in contracts:
                    addr = vertrag["address"]
                    display = f"{addr['city']}, {addr['street']} {addr['houseNumber']} ({addr['zip']}) [{vertrag['id']}]"
                    contract_choices[vertrag["id"]] = display
                self.contract_choices = contract_choices
                return await self.async_step_select_contract()    

            except InvalidAuth:
                errors["base"] = "invalid_auth"
                _LOGGER.warning("user "+user_input["apiuser"])
            except Exception:  
                 _LOGGER.exception("Unexpected exception")
                 errors["base"] = "unknown"       
               
            #if result:
            return self.async_create_entry(title="myostrom", data=user_input)
           #else:
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
        
        async def async_step_select_contract(self, user_input: dict[str, Any] | None = None):
            contract_schema = vol.Schema({
                vol.Required("contract_id"): vol.In(self.contract_choices),
                vol.Optional("want_consumption", default=False): bool
            })
            errors = {}
            if user_input is not None:
                contract_id = user_input["contract_id"]
                want_consumption = user_input["want_consumption"]
            self._set_unique_id(contract_id)
            self._abort_if_unique_id_configured()
            # Suche die Adresse im choices
            address = self.contract_choices[contract_id]
            # Entry anlegen mit allen Daten
            entry_data = {
                "contract_id": contract_id,
                "address": address,
                "want_consumption": want_consumption
            }
            return self.async_create_entry(
                title=f"Ostrom {address}",
                data=entry_data
            )
        return self.async_show_form(
            step_id="select_contract", data_schema=contract_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
    
class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""    
        
        
