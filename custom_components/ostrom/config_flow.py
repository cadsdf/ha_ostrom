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

    VERSION = 5

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle inital step."""
        errors = {}
        if user_input is not None:
           self.data = user_input
           # Create a unique ID:
           _unique_id = self.data['apiuser'][:8]
           
           try:
               info = await validate_input(self.hass, user_input)
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
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS_SCHEMA,
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
    
class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""    
        
        
