""" ConfigFlow for Ostrom """

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError


from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)

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
            self.apiuser = user_input["apiuser"]
            self.apipass = user_input["apipass"]
            # lege die Api an
            data = user_input
            self.api = OstromApi(data["apiuser"], data["apipass"],self.hass.loop)
            try:
                # test zugangsdaten
                await self.api.ostrom_outh()  
                # alle verträge holen
                contracts = await self.api.ostrom_contracts()
                self.contracts = contracts  # <-- Liste speichern!
                self.contract_choices = {}
                for vertrag in contracts:
                    addr = vertrag["address"]
                    display = f"{addr['city']}, {addr['street']} {addr['houseNumber']} ({addr['zip']}) [{vertrag['id']}]"
                    self.contract_choices[str(vertrag["id"])] = display
                return await self.async_step_select_contract()    

            except InvalidAuth:
                errors["base"] = "invalid_auth"
                _LOGGER.warning("user "+user_input["apiuser"])
            except Exception:  
                 _LOGGER.exception("Unexpected exception")
                 errors["base"] = "unknown"       
               
           # return self.async_create_entry(title="myostrom", data=user_input)
       
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
        
    async def async_step_select_contract(self, user_input: dict[str, Any] | None = None):
        contract_schema = vol.Schema({
            vol.Required("contract_id"): vol.In(self.contract_choices)
        })
        errors = {}
        if user_input is not None:
            contract_id = user_input["contract_id"]
            await self.async_set_unique_id(contract_id)
            self._abort_if_unique_id_configured()
 
            selected_contract = next(
                (c for c in self.contracts if str(c["id"]) == str(contract_id)),
                None
            )
            if selected_contract is None:
                errors["base"] = "invalid_contract"
            else:
                addr = selected_contract.get("address", {})
                zip_code = addr.get("zip", "")
                address = f"{addr.get('city','')}, {addr.get('street','')} {addr.get('houseNumber','')} ({zip_code})"
                entry_data = {
                    "apiuser": self.apiuser,          # Zugangsdaten mitgeben!
                    "apipass": self.apipass,
                    "contract_id": contract_id,
                    "zip": zip_code,
                    "address": address,
                }
                return self.async_create_entry(
                    title=f"Ostrom {address}",
                    data=entry_data
                )
         
        return self.async_show_form(
            step_id="select_contract", data_schema=contract_schema, errors=errors
        )
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OstromOptionsFlowHandler(config_entry)    
        
        
class OstromOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Ostrom."""

    #def __init__(self, config_entry):
        #self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        # Default value from config_entry.options or fallback to False
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(OPTION_BOOL_KEY, default=self.config_entry.options.get(OPTION_BOOL_KEY, False)): bool,
            }),
        )        


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
    
class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""    
        
        
