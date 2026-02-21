# Home Assistant Ostrom Integration

Mit dieser Custom Component kannst du die aktuellen und historischen Strompreise sowie Verbrauchsdaten von Stromanbieter Ostrom direkt in Home Assistant anzeigen und auswerten. HACS ist vorraussetzung!

## Version 5

Refaktorierte Codebase mit typisierten Datenmodellen und zusätzlichen Sensoren.

### Änderungen

- Refaktorierte Integrationsarchitektur mit typisierten Modulen:
  - `ostrom_api_client.py` für HTTP/Authentifizierung
  - `ostrom_provider.py` für Provider-Logik und Datenaktualisierung
  - `ostrom_data.py` für typisierte Datenmodelle

- Erweitertes Entitätsmodell:
  - dedizierte Sensoren für aktuelle Preisbestandteile, monatliche Gebühren und Minimum-Preis-Zeitfenster
  - dedizierte Zeitsensoren für alle Minimum-Preis-Ziele
  - manueller Aktualisierungs-Button `button.ostrom_refresh_data`
  - Entitäten werden jetzt unter einem gemeinsamen Home-Assistant-Gerät zusammengefasst, inklusive Gesamtübersicht aller zugehörigen Entitäten

- Ruff Linting-Workflow für lokale Entwicklung

- Dev-Skripte im Project Root ergänzt:
  - `ostrom.py` für direkte Datenabfrage und API-Tests
  - `ostrom_visualization.py` für die Visualisierung von Verbrauchs- und Spotpreis-Daten mit `matplotlib`

- Implementiert mit GPT-5.3-Codex Pair-Programming-Support

### Entitäten

#### Sensoren
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

#### Binary Sensoren
- `binary_sensor.ostrom_lowest_price_is_now`

#### Buttons
- `button.ostrom_refresh_data`

Hinweis: Die exakten Entity IDs können abweichen, wenn Entitäten in Home Assistant umbenannt wurden.

### Forecast-Attribute

`sensor.ostrom_forecast` stellt chart-kompatible Attribute bereit:

- `forecast`: Liste mit `{datetime, value}`-Einträgen
- `data`: Kompatibilitätsliste mit `{date, price}` für Karten, die dieses Format erwarten
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

### ApexCharts-Beispiel

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

### Präzision / Einheiten

- EUR/kWh-Sensoren verwenden 4 Nachkommastellen (empfohlene Anzeigepräzision)
- Monatliche EUR-Gebührensensoren verwenden 2 Nachkommastellen (empfohlene Anzeigepräzision)

### Entwicklung

#### Lokale Skripte
- `ostrom.py`: lokales API-/Testskript
- `ostrom_visualization.py`: lokaler Visualisierungs-Helper
- `tests/`: integrationsbezogene Tests

#### Lint / Tests
```bash
ruff check custom_components/ostrom tests
pytest -q
```

## Version 4
- **diese version 4 wurde mit hilfe von copilot entwickelt - hat mir sehr geholfen als Anfängerin in Homassistant custom Component Entwickung
- ** gegen der alten Version ist alles anders - sensor ostrom.price wurde zu sensor.ostrom_raw_forcast_data_1 - wenn alte version verwendet wird ist leider dann viel anpassung nötig - sorry 
- ** für die Anzeige der Daten wird weiterhin apexchart-card benötigt (hacs) https://github.com/RomRider/apexcharts-card Beispiele hier: https://github.com/melmager/ha_ostrom/blob/version4/apex/de_apex_anzeige.md
- ** als Verbrauchszähler muss man den HA-custom-component-energy-meter (hacs) nutzen - der Energiemeter von Homeassistant kennt / kann keine dynamischen Tarife ! https://github.com/zeronounours/HA-custom-component-energy-meter
- ** Beschreibung der verwendeten API von Ostrom : https://docs.ostrom-api.io/reference/introduction

## Features

- **Aktueller Strompreis**: Anzeige des aktuellen Preises EUR pro kWh.
- **Preishistorie (48h)**: Rückblick auf Kosten vor 48 Stunden mit Attribute Preis und Verbrauch (aber nur wenn ein IMSYS (Smartmeter mit Kommunikationsmodule) und Option gesetzt wurde) vorhanden ist ! Leider hat HA ein Problem mit alten Sensordaten, Der Sensor wird von HA mit aktueller Zeit erstellt, aber die Daten sind 48 Stunden alt !
- **Niedrigster Preis als Binary Sensor**: Zeigt an, ob gerade der niedrigste Preis im aktuellen Forecast erreicht ist.
- **Mehrere Verträge auswählbar**: Bei mehreren Verträgen kannst du im Setup einen auswählen.
- **Automatische Aktualisierung**: Die Daten werden stündlich aktualisiert. Die Automatisierung die stündlich ein Service aufruf aus Version 3 ist unnötig geworden.

## Installation

1. HACS - Benutzerdefinierte Repositories - Repository: "melmager
/
ha_ostrom" Type: Integration
2. Starte Home Assistant neu. Dann ist `/config/custom_components/ostrom/` in deiner Home Assistant Installation vorhanden

## Einrichtung

1. Gehe in Home Assistant zu **Einstellungen > Integrationen** und füge die Integration „Ostrom“ hinzu.
2. Gib deine API-Zugangsdaten an (`apiuser`, `apipass`). Müssen hier erstellt werden :  https://developer.ostrom-api.io/auth/login 
3. Wähle deinen Stromvertrag aus der Liste aus.
4. Optional: Aktiviere die Verbrauchsanzeige für die letzten 48 Stunden. Nur mit IMSYS möglich (Digitalzähler mit Komminkationsmodule) ! Wenn die Option für den Kostensensor in der Integration gesetzt wurde bitte "neu laden" - erst dann taucht der Sensor auf - das liegt an HA.

## Sensoren

| Sensor                 | Beschreibung / Attribute                      |                       
|------------------------|-----------------------------------------------|
| Ostrom Actual Price    | Aktueller Preis in EUR/kWh                    |
|                        | ID : ostrom_actualprice_(vertragsnr)          |
| Cost 48h Past          | Stromkosten der Stunde vor 48 Stunden ( in EUR) (Opton gesetzt?)|
|                        | ID : eindeutige Sensor ID                     |
|                        | consum : Stromverbrauch in kWh                |
|                        | price : Strompreis kwh in cent                |
|                        | time : messzeitpunkt                          |
|                        | Date mismatch : true wenn Zeitpunkt Strompreis gleich Stromverbrauch ist - sollte True sein |
| Ostrom Raw forcast data| Rohdaten des Preisforecasts (genutzt z.B von Apex-chart)  Status kWh Price in cent |
|                        | Average : Durchschnittspreis aller forcast daten in cent|
|                        | low : Niedrigster Preis - price / date        |
|                        | data : forcast daten stündlich - price / date |
| Lowest Price Now       | Binary Sensor: Ist gerade günstigster Preis? centelcent genau|
| Ostrom API Status      | War letze Abfrage erfolgreich - Normal OK     |
|                        | Last error : Fehler der aufgetreten ist       |
|                        | Last time : Zeitpunkt letzte abfrage          |

## Optionen

- **use_past_sensor**: Zeigt Kosten/Verbrauch vor 48h an (optional) - IMSYS nötig ob Verbrauchsdaten geliefert werden kann man in der Ostrom App erkennen. Fehler wenn keine Daten geliefert werden!

## Beispiel für Automationen

```
alias: Happy Hour Strompreis
description: 'Benachrichtige, wenn der Niedrigstpreis erreicht ist.'
trigger:
  - platform: state
    entity_id: binary_sensor.lowest_price_now_1  # ggf. anpassen!
    to: 'on'
action:
  - service: notify.mobile_app_dein_gerät  # anpassen!
    data:
      message: >
        Happy Hour Strompreis ist bei {{ states('sensor.actual_price_1') | float(default=0) * 100 | round(1) }} Cent/kWh!
      title: "Happy Hour Strom!"
mode: single

```

## Troubleshooting

- Prüfe die Home Assistant Logs auf API-Fehler.
- Stelle sicher, dass deine Zugangsdaten korrekt sind.
- Bei Fragen oder Problemen: [GitHub Issues](https://github.com/melmager/ha_ostrom/issues)

## Lizenz

MIT License

---

Viel Spaß mit günstigerem Strom und smartem Monitoring!

Falls einer noch kein Ostrom Kunde ist unter https://github.com/melmager/ha_ostrom/blob/main/promo.text ist mein Promocode den man bei Neuvertrag angeben kann und ich dadurch eine Prämie bekomme.

oder: 

<a href="https://www.buymeacoffee.com/taunushexe" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

Ich bin auch nur Kundin bei Ostrom - ist keine offizielle Software vom Stromanbieter Ostrom ! Keine Haftung bei Einsatz meine Software :-)
