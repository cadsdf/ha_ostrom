from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

class Ostrom_Price_Now(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Actual Price"
        self._attr_native_unit_of_measurement = "EUR/kWh"
        self._attr_unique_id = "ostrom_price_now"
        self._attr_icon = "mdi:currency-eur"

    @property
    def native_value(self):
        return self.coordinator.data.get("actual_price")
        
class Ostrom_Price_Raw(CoordinatorEntity, SensorEntity):
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ostrom Raw forcast Data"
        self._attr_unique_id = "ostrom_price_rawdata"
        self._attr_icon = "mdi:chart-timeline-variant"

    @property
    def native_value(self):
        return self.coordinator.data.get("cost_48h_past")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "average": data.get("consum"),
            "low": data.get("price"),
            "data": data.get("time"),
        }
        

class Cost_48hPast(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cost 48h Past"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_unique_id = "ostrom_cost_48h_past"
        self._attr_device_class = "monetary"
        self._attr_icon = "mdi:currency-eur"


    @property
    def native_value(self):
        return self.coordinator.data.get("cost_48h_past")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "consum": data.get("consum"),
            "price": data.get("price"),
            "time": data.get("time"),
        }


class LowestPriceNowBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Lowest Price Now"
        self._attr_unique_id = "ostrom_lowest_price_now"
        self._attr_device_class = "power"
        self._attr_icon = "mdi:power-plug"

    @property
    def is_on(self):
        #current = self.coordinator.data.get("actual_price")
        forecast = self.coordinator.data.get("forecast_prices", [])
        #if not forecast or current is None:
        #    return False
        #min_price = min([p["price"] for p in forecast])
        return forecast["low"]["price"] == forecast["data"][0]["price"]

    
async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        Ostrom_Price_Raw(coordinator),
        Ostrom_Price_Now(coordinator),
        LowestPriceNowBinary(coordinator),
    ]
    if config_entry.options.get("use_past_sensor", False):
        entities.append(Cost_48hPast(coordinator))

    async_add_entities(entities)    