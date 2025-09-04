# Home Assistant Ostrom Integration

This custom component allows you to display and analyze current and historical electricity prices as well as consumption data from the electricity provider Ostrom directly in Home Assistant. **HACS is required!**

[Deutsche Version / German version here](./DE-README.md)

## Version 4
- **This version 4 was developed with the help of Copilot – it was a great help for me as a beginner in Home Assistant custom component development!**
- **Everything is different compared to the old version – the sensor `ostrom.price` has become `sensor.ostrom_raw_forcast_data_1`. If you are upgrading from an older version, you will need to make a lot of adjustments – sorry!**
- **To display the data, you still need the apexchart-card (HACS) https://github.com/RomRider/apexcharts-card. See examples here: https://github.com/melmager/ha_ostrom/tree/main/apex**
- **For energy metering, you must use the HA-custom-component-energy-meter (HACS) – Home Assistant’s built-in energy meter does not support dynamic tariffs! https://github.com/zeronounours/HA-custom-component-energy-meter**
- **API documentation used by this integration: https://docs.ostrom-api.io/reference/introduction**

## Features

- **Current electricity price**: Shows the current price in EUR per kWh.
- **Price history (48h)**: View costs from 48 hours ago with price and consumption attributes (only if an IMSYS (smart meter with communication module) is available! Unfortunately, Home Assistant has a problem with old sensor data – the sensor is timestamped with the current time, but the data is 48 hours old!)
- **Lowest price as binary sensor**: Indicates whether the lowest price in the current forecast is active.
- **Select from multiple contracts**: If you have several contracts, you can choose one during setup.
- **Automatic updates**: Data is updated hourly. The automation that called a service hourly in version 3 is no longer needed.

## Installation

1. In HACS, go to Custom Repositories – Repository: "melmager/ha_ostrom", Type: Integration
2. Restart Home Assistant. The directory `/config/custom_components/ostrom/` will now exist in your Home Assistant installation.

## Setup

1. In Home Assistant, go to **Settings > Integrations** and add the “Ostrom” integration.
2. Enter your API credentials (`apiuser`, `apipass`). Credentials must be created here: https://developer.ostrom-api.io/auth/login
3. Select your electricity contract from the list.
4. Optional: Enable consumption display for the last 48 hours. Only possible with IMSYS! If the option was set in the integration, please "reload" - only then will the sensor appear - this is due to HA.


## Sensors

| Sensor                | Description                                      |
|-----------------------|--------------------------------------------------|
| Actual Price          | Current price in EUR/kWh                         |
| Cost 48h Past         | Total cost over the last 48 hours (EUR) (option enabled?) |
| Ostrom Raw forecast   | Raw price forecast data (used e.g. by Apex-chart)|
| Lowest Price Now      | Binary sensor: Is it currently the lowest price? |

## Options

- **use_past_sensor**: Shows cost/consumption from 48h ago (optional) – IMSYS is required. You can check in the Ostrom app whether consumption data is available. If no data is supplied, you’ll see an error!

## Example Automation

```yaml
alias: Happy Hour Electricity Price
description: 'Notify when the lowest electricity price is reached.'
trigger:
  - platform: state
    entity_id: binary_sensor.lowest_price_now_1  # Adjust to your sensor!
    to: 'on'
action:
  - service: notify.mobile_app_your_device  # Change to your notification service!
    data:
      message: >
        Happy Hour! Electricity price is now {{ states('sensor.actual_price_1') | float(default=0) * 100 | round(1) }} cents/kWh!
      title: "Happy Hour Power"
mode: single

```

## Troubleshooting

- Check the Home Assistant logs for API errors.
- Make sure your credentials are correct.
- For questions or issues: [GitHub Issues](https://github.com/melmager/ha_ostrom/issues)

## License

MIT License

---

Enjoy cheaper electricity and smart monitoring!

If you are not yet an Ostrom customer, my promo code is available under promo.text – you can enter it for a new contract and I will receive a bonus.

Or:

<a href="https://www.buymeacoffee.com/taunushexe" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

I am just a customer at Ostrom – this is **not** official software from Ostrom! No liability for using my software :-)
