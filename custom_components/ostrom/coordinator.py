"""Integration 101 Template integration using DataUpdateCoordinator."""

from datetime import timedelta, datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_change

from .ostrom_api import OstromApi, APIConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_get_data(lnk_api,get_cost):
    # Replace with your actual async data fetching logic
    # For example, fetch from API or storage
    return {
        "price_48h_past": 0.25,
        "consum": 12.5,
        "price": 3.12,
        "time": "2025-08-20T01:01:00Z",
    }

class OstromCoordinator(DataUpdateCoordinator):
    
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        apiuser = config_entry.data.get("apiuser")
        apipass = config_entry.data.get("apipass")
        self.api_client = OstromApi(apiuser, apipass, hass.loop)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            # No update_interval, we'll trigger manually at minute 1 every hour
        )
        self._hass = hass
        self.isinit = False 
        
    async def _async_update_data(self):
        if not self.isinit:
            await self.api_client.ostrom_outh()
            await self.api_client.ostrom_contracts()
            self.isinit = True
        ostromdaten = {"cost_48h_past":0,"price":0,"time":"2025-08-03T12:00:00Z","past":"2025-08-01T12:00:00Z","raw":""}
        erg = await self.api_client.get_forecast_prices()
        ostromdaten["price"] = erg["data"][0]["price"] / 100
        ostromdaten["time"] = erg["data"][0]["date"]
        ostromdaten["raw"] = erg
        return ostromdaten

    async def async_setup_hourly_update(self):
        
        async def hourly_update(now):
            _LOGGER.debug("Triggering hourly update at minute 1")
            await self.async_refresh()

        # Schedule update at minute 1 every hour
        async_track_time_change(
            self._hass,
            hourly_update,
            minute=1,
            second=0,
        )
        
        
