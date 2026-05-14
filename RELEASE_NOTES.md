# Release Notes

## 0.5.3

### Fixed

- Keep Ostrom sensors available during transient API update failures so existing
  readings remain visible instead of becoming unavailable.
- Keep the manual refresh button available when the latest coordinator update
  failed, allowing users to retry immediately from Home Assistant.
- Continue reporting API health through the Ostrom Status sensor, which changes
  to `Error` and exposes the failure details while other entities retain their
  last known values.
- Track and cancel scheduled retry callbacks so repeated update failures do not
  accumulate duplicate retry timers.

### Tests

- Added regression coverage for entity availability after update failures.
- Enabled async pytest configuration so Home Assistant async tests execute
  instead of being skipped.

## 0.5.2

Refactored codebase with typed data models and additional sensors.

### Changes

- Refactored integration architecture into typed modules:
  - `ostrom_api_client.py` for HTTP/auth
  - `ostrom_provider.py` for provider logic
  - `ostrom_data.py` for typed data models

- Expanded entity model:
  - sensors for current prices, monthly fees, consumption totals, and minimum-price windows
  - timestamp sensors for all minimum-price targets and contract metadata
  - refresh button for manual data update `button.ostrom_refresh_data`
  - refresh service for automations `ostrom.refresh_data`
  - integration entities are grouped under a single Home Assistant device for a consolidated overview

- Added integration test scaffolding for config flow, coordinator behavior, and entity output
- Added Ruff linting workflow for local development

- Added root-level development scripts for local API access and visualization:
  - `ostrom.py` for direct data retrieval / testing
  - `ostrom_visualization.py` for consumption and spot-price plots with `matplotlib`

- Implemented with GPT-5.3-Codex pair programming support