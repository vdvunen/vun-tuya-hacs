# VUN Tuya — Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA versie](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

Home Assistant integratie die verbindt met een **VUN-Tuya-Hassio** server (v3.1.2+). Alle Tuya-synchronisatie en apparaatbeheer verloopt via die server — in HA verschijnen de apparaten als native entities.

---

## Functies

- **Verbindt met VUN-Tuya-Hassio** — geen aparte Tuya API-sleutels nodig in HA
- **Lokale LAN-besturing** — commando's gaan via de VUN-server direct naar het apparaat
- **Meerdere platformtypes**: licht, schakelaar, klimaat, sensor, binaire sensor, ventilator, rolluik, slot, stofzuiger, alarm, deurbel
- **Automatische entity-detectie** — alle bevestigde entities in VUN-Tuya-Hassio verschijnen automatisch
- **Mapping-gebaseerd** — gebruikt de DP-mappings uit VUN-Tuya-Hassio voor correcte attribuut-koppeling
- **Config flow** — eenvoudig in te stellen via de HA UI, alleen server-adres nodig

---

## Vereisten

- Home Assistant 2024.1 of nieuwer
- Een draaiende **VUN-Tuya-Hassio** server v3.1.2 of nieuwer (bereikbaar via het netwerk vanuit HA)
- Minimaal één bevestigde entity in VUN-Tuya-Hassio

---

## Installatie via HACS

1. Open HACS → Integraties → rechtsboven de drie stippen → **Aangepaste repository's**
2. Voeg `https://github.com/vdvunen/vun-tuya-hacs` toe als type **Integratie**
3. Zoek naar **VUN Tuya** en installeer
4. Herstart Home Assistant
5. Ga naar **Instellingen → Apparaten & Services → Integratie toevoegen**
6. Zoek op **VUN Tuya** en volg de installatiewizard

---

## Handmatige installatie

1. Download de laatste release van GitHub
2. Kopieer de map `custom_components/vun_tuya` naar `<config>/custom_components/`
3. Herstart Home Assistant
4. Voeg de integratie toe via de UI

---

## Configuratie

### Stap 1 — VUN-Tuya-Hassio

Zorg dat de VUN-Tuya-Hassio server draait en dat er bevestigde entities zijn (status = confirmed). Standaard draait de server op poort **7654**.

Als auth ingeschakeld is in VUN-Tuya-Hassio, maak dan een API-sleutel aan via **Instellingen → Gebruikers** in de VUN-webinterface.

### Stap 2 — HA integratie

| Veld | Beschrijving |
|------|-------------|
| Server adres | Volledig adres van VUN-Tuya-Hassio, bijv. `http://192.168.1.100:7654` |
| API-sleutel | Optioneel — alleen nodig als auth ingeschakeld is |

### Opties (aanpasbaar na installatie)

| Optie | Standaard | Beschrijving |
|-------|-----------|-------------|
| Polling interval | 30 sec | Hoe vaak de device status wordt ververst |

---

## Ondersteunde apparaattypen

| Categorie | Tuya codes | Platform |
|-----------|-----------|---------|
| Verlichting | dj, dd, fwd, dc, tgq, xdd | light |
| Ventilator | fs, fsd, fskg | fan |
| Schakelaar | kg, tgkg, cz, pc, dlq | switch |
| Klimaat | kt, wnykq, qn, rs, wk, wkf | climate |
| Sensor | wsdcg, co2bj, pm25, ldcg | sensor |
| Bewegingssensor | pir | binary_sensor |
| Deursensor | mcs | binary_sensor |
| Rooksensor | ywbj | binary_sensor |
| Videodeurbel | sp, dbl, sp2, ds | binary_sensor |
| Rolluik / gordijn | cl, clkg, wkcz | cover |
| Slim slot | ms, jtmspro, videolock | lock |
| Robotstofzuiger | sd, sweeper, mop, sz, sdmop | vacuum |
| Alarmpaneel | alarm, wg, mal | alarm_control_panel |

---

## Bekende beperkingen

- Apparaten die **alleen via Bluetooth** werken worden niet ondersteund (geen LAN)
- Protocol 3.4/3.5 apparaten werken wel maar vereisen dat de local key correct in de Tuya Cloud staat
- De integratie gebruikt `nowait=True` voor SET-commando's omdat veel Tuya-apparaten geen ACK sturen

---

## Problemen melden

Dien een issue in op [GitHub Issues](https://github.com/vdvunen/vun-tuya-hacs/issues).

---

## Licentie

MIT License — zie [LICENSE](LICENSE) voor details.
