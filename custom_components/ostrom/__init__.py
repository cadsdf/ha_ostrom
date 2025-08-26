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
import json

from .ostrom_api import *

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

CONF_TOPIC = 'ostrom_login setup'

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Ostrom from yaml (old version)."""
    if DOMAIN in config:
        hass.data[DOMAIN] = await hass.async_add_executor_job(
            ostrom_ha_setup, config[DOMAIN]["apiuser"], config[DOMAIN]["apipass"]
        )
    return True
    

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = OstromDataCoordinator(hass, entry)
    await coordinator.async_setup_hourly_update()
    await coordinator.async_config_entry_first_refresh()
    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True
    

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok    
    


