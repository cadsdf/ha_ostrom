# Home Assistant Ostrom Integration

This custom component allows you to display and analyze current and historical electricity prices and consumption data from the electricity provider Ostrom directly in Home Assistant. **HACS is required!**

**[Deutsche Version/Readme hier](DE-README.md)**

## Version 5

Refactored codebase with typed data models and additional sensors.

### Changes

- Refactored integration architecture into typed modules:
  - `ostrom_api_client.py` for HTTP/auth
  - `ostrom_provider.py` for provider logic
  - `ostrom_data.py` for typed data models

- Expanded entity model:
  - dedicated sensors for current price parts, monthly fees, and minimum-price windows
  - dedicated timestamp sensors for all minimum-price targets
  - manual refresh button `button.ostrom_refresh_data`
  - integration entities are now grouped under a single Home Assistant device for a consolidated entity overview

- Added Ruff linting workflow for local development

- Added root-level development scripts for local API access and visualization:
  - `ostrom.py` for direct data retrieval / testing
  - `ostrom_visualization.py` for consumption and spot-price plots with `matplotlib`

- Implemented with GPT-5.3-Codex pair programming support


### Entities

#### Sensors
- `sensor.ostrom_status`
- `sensor.ostrom_current_electricity_price`
- `sensor.ostrom_current_net_energy_price`
- `sensor.ostrom_current_taxes_and_levies`
- `sensor.ostrom_forecast`
- `sensor.ostrom_monthly_base_fee`
- `sensor.ostrom_monthly_grid_fee`
- `sensor.ostrom_monthly_fees`
- `sensor.ostrom_minimum_price_today`
- `sensor.ostrom_minimum_price_upcoming_today`
- `sensor.ostrom_minimum_price_tomorrow`
- `sensor.ostrom_minimum_price_all_available`
- `sensor.ostrom_minimum_price_today_time`
- `sensor.ostrom_minimum_price_upcoming_today_time`
- `sensor.ostrom_minimum_price_tomorrow_time`
- `sensor.ostrom_minimum_price_all_available_time`

#### Binary Sensors
- `binary_sensor.ostrom_lowest_price_is_now`

#### Buttons
- `button.ostrom_refresh_data`

Note: exact entity IDs can vary if names are customized in Home Assistant.

### Forecast Attributes

`sensor.ostrom_forecast` exposes chart-ready attributes:

- `forecast`: list of `{datetime, value}` entries
- `data`: compatibility list of `{date, price}` entries (for cards expecting legacy keys)
- `minimum_price_today`
- `minimum_price_upcoming_today`
- `minimum_price_tomorrow`
- `minimum_price_all_available`
- `lowest_price`
- `lowest_price_time`
- `forecast_count`
- `forecast_first`
- `forecast_last`
- `forecast_future_count`

### ApexCharts Example

```yaml
type: custom:apexcharts-card
graph_span: 48h
span:
  start: hour
  offset: "-12h"
series:
  - entity: sensor.ostrom_forecast
    name: Ostrom Forecast
    data_generator: |
      return (entity.attributes.data || []).map((row) => {
        return [new Date(row.date).getTime(), row.price];
      });
```

### Precision / Units

- EUR/kWh sensors use 4 decimals (suggested display precision)
- EUR monthly fee sensors use 2 decimals (suggested display precision)

### Development

#### Local scripts
- `ostrom.py`: local API/testing script
- `ostrom_visualization.py`: visualization helper script
- `tests/`: integration-focused tests

#### Lint / tests
```bash
ruff check custom_components/ostrom tests
pytest -q
```

## Version 4
- **This version 4 was developed with help from Copilot – it was very helpful for me as a beginner in Home Assistant custom component development.**
- **Compared to the old version, everything is different – the sensor ostrom.price was changed to sensor.ostrom_raw_forcast_data_1. If you were using the old version, you will unfortunately need to make many adjustments – sorry!**
- **To display the data, you still need the apexchart-card (HACS): https://github.com/RomRider/apexcharts-card. Example configurations: https://github.com/melmager/ha_ostrom/blob/version4/apex/de_apex_anzeige.md  **
- **For consumption metering, you must use the HA-custom-component-energy-meter (HACS) – Home Assistant's built-in energy meter does not support dynamic tariffs! https://github.com/zeronounours/HA-custom-component-energy-meter**
- **Description of the Ostrom API used: https://docs.ostrom-api.io/reference/introduction**

## Features

- **Current electricity price**: Displays the current price in EUR per kWh.
- **Price history (48h)**: Shows the cost 48 hours ago with attributes for price and consumption (only available if you have an IMSYS [smart meter with communication module] and the option is enabled). Unfortunately, Home Assistant has an issue with old sensor data: the sensor is created with the current time, but the data is 48 hours old!
- **Lowest price as binary sensor**: Indicates whether the lowest price in the current forecast is currently reached.
- **Multiple contracts selectable**: If you have several contracts, you can select one during setup.
- **Automatic updates**: Data is updated hourly. The hourly service call automation from version 3 is no longer necessary.

## Installation

1. In HACS, go to Custom Repositories – Repository: "melmager/ha_ostrom" Type: Integration
2. Restart Home Assistant. `/config/custom_components/ostrom/` will now be present in your installation.

## Setup

1. In Home Assistant, go to **Settings > Integrations** and add the “Ostrom” integration.
2. Enter your API credentials (`apiuser`, `apipass`). You must create them here: https://developer.ostrom-api.io/auth/login
3. Select your electricity contract from the list.
4. Optionally: Enable display of consumption for the last 48 hours. Only possible with IMSYS (digital meter with communication module)! If you enable the cost sensor option, please "reload" the integration – only then will the sensor appear (this is a limitation of Home Assistant).

## Sensors

| Sensor                    | Description / Attributes                                  |                       
|---------------------------|----------------------------------------------------------|
| Ostrom Actual Price       | Current price in EUR/kWh                                 |
|                           | ID: ostrom_actualprice_(contract number)                 |
| Cost 48h Past             | Electricity cost for the hour 48 hours ago (in EUR) (option set?)|
|                           | Unique sensor ID                                         |
|                           | consum: electricity consumption in kWh                   |
|                           | price: electricity price in cent                         |
|                           | time: measurement timestamp                              |
|                           | Date mismatch: true if price and consumption timestamps match – should be true |
| Ostrom Raw forecast data  | Raw data of price forecast (used e.g. by Apex-chart)     |
|                           | Average: average price of all forecast data in cent      |
|                           | low: lowest price – price / date                         |
|                           | data: forecast data hourly – price / date                |
| Lowest Price Now          | Binary Sensor: Is the lowest price currently reached? (exact to two decimals)|
| Ostrom API Status         | Was the last query successful? Normally OK               |
|                           | Last error: last error that occurred                     |
|                           | Last time: timestamp of last query                       |

## Options

- **use_past_sensor**: Shows cost/consumption 48 hours ago (optional) – IMSYS required to retrieve consumption data (check in the Ostrom app). Error if no data is available!

## Example Automation

```yaml
alias: Happy Hour Electricity Price
description: 'Notify when the lowest price is reached.'
trigger:
  - platform: state
    entity_id: binary_sensor.lowest_price_now_1  # adjust as needed!
    to: 'on'
action:
  - service: notify.mobile_app_your_device  # adjust as needed!
    data:
      message: >
        Happy Hour: Electricity price is {{ states('sensor.actual_price_1') | float(default=0) * 100 | round(1) }} Cent/kWh!
      title: "Happy Hour Electricity!"
mode: single
```

## Troubleshooting

- Check Home Assistant logs for API errors.
- Make sure your credentials are correct.
- For questions or problems: [GitHub Issues](https://github.com/melmager/ha_ostrom/issues)

## License

MIT License

---

Enjoy cheaper electricity and smart monitoring!

If you are not yet an Ostrom customer, you can find my promo code at https://github.com/melmager/ha_ostrom/blob/main/promo.text – if you enter it when signing up for a new contract, I receive a bonus.

or: 

<a href="https://www.buymeacoffee.com/taunushexe" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

I am just a customer at Ostrom – this is not official software from the electricity provider! No liability for using my software :-)
