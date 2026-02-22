"""Constants for Ostrom electricity provider integration."""

DOMAIN: str = "ostrom"
SERVICE_REFRESH_DATA: str = "refresh_data"
DEFAULT_SCAN_INTERVAL: int = 60

# Icons
ICON: str = "mdi:current-ac"
ICON_COST: str = "mdi:currency-eur"
ICON_PLUG: str = "mdi:power-plug"
ICON_GRID: str = "mdi:transmission-tower"
ICON_CASH: str = "mdi:account-cash-outline"

# Component specific attributes
FAIL_RETRY_INTERVAL_MINUTES: int = 10

# API constants
KEY_ADDRESS: str = "address"
KEY_PASSWORD: str = "password"
KEY_USER: str = "user"
KEY_CONTRACT_INDEX: str = "contract_index"
KEY_DATA: str = "data"
KEY_CONTRACT_ID: str = "contract_id"
KEY_PRICE: str = "price"
KEY_CITY: str = "city"
KEY_STREET: str = "street"
KEY_HOUSE_NUMBER: str = "house_number"
KEY_ZIP_CODE: str = "zip"

# Unit definitions
# Does not seem to exist in homeassistant.const
UNIT_EURO_PER_KWH: str = "EUR/kWh"
