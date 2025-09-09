# Home Assistant Ostrom Integration

Mit dieser Custom Component kannst du die aktuellen und historischen Strompreise sowie Verbrauchsdaten von Stromanbieter Ostrom direkt in Home Assistant anzeigen und auswerten. HACS ist vorraussetzung!

## Version 4
- **diese version 4 wurde mit hilfe von copilot entwickelt - hat mir sehr geholfen als Anfängerin in Homassistant custom Component Entwickung
- ** gegen der alten Version ist alles anders - sensor ostrom.price wurde zu sensor.ostrom_raw_forcast_data_1 - wenn alte version verwendet wird ist leider dann viel anpassung nötig - sorry 
- ** für die Anzeige der Daten wird weiterhin apexchart-card benötigt (hacs) https://github.com/RomRider/apexcharts-card Beispiele hier: https://github.com/melmager/ha_ostrom/tree/main/apex/de_apex_anzeige.md
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
