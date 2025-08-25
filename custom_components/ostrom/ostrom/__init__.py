"""
Configuration:
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
#from homeassistant.util.json import JsonObjectType as json
import logging
from .coordinator import OstromDataCoordinator

import asyncio
import datetime
#import timedelta
import logging
import requests
import json
import base64
import math
from .ostrom_api import *

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

CONF_TOPIC = 'ostrom_login setup'

_LOGGER = logging.getLogger(__name__)

    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
        
    #api_client = OstromApi(entry.data["apiuser"],entry.data["apipass"])
    # Example: YourAPIClient(entry.data["apiuser"], entry.data["apipass"])

    # Create the coordinator instance
    coordinator = OstromDataCoordinator(hass,entry)
    
    await coordinator.async_setup_hourly_update()
    await coordinator.async_config_entry_first_refresh()
    
    entities = [
        Ostrom_Price_Now(coordinator),
        LowestPriceNowBinarySensor(coordinator),
    ]
    if config_entry.options.get("cost_48h_past_enabled", False):
        entities.append(Cost_48hPastSensor(coordinator))

    async_add_entities(entities)

    # Save the coordinator in hass.data under DOMAIN and entry_id
    hass.data.setdefault(DOMAIN, {})  # Ensure DOMAIN dict exists
    hass.data[DOMAIN][entry.entry_id] = coordinator
    

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok    
    
