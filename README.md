# VUN Tuya — Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA versie](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

Lokale Tuya-integratie voor Home Assistant met Tuya Cloud sync voor local keys. Bestuurt apparaten **rechtstreeks via het lokale netwerk** (LAN), zonder Cloud-afhankelijkheid bij gebruik.

---

## Functies

- **Lokale LAN-besturing** — commando's gaan direct naar het apparaat, niet via de Tuya Cloud
- **Automatische Cloud sync** — haalt local keys en apparaatlijst op via de Tuya IoT API
- **Cloud fallback** — als lokale besturing mislukt, valt het terug op de Tuya Cloud API
- **Meerdere platformtypes**: licht, schakelaar, klimaat, sensor, binaire sensor, ventilator, rolluik, slot, stofzuiger, alarm, deurbel
- **Energie-meting** — vermogen, stroom, spanning, energie voor slimme stekkers
- **Config flow** — eenvoudig in te stellen via de HA UI, geen YAML nodig
- **Options flow** — polling interval en subnet aanpasbaar na installatie

---

## Vereisten

- Home Assistant 2024.1 of nieuwer
- Een [Tuya IoT Platform](https://iot.tuya.com/) account met een Cloud project
- API Key (Client ID) en API Secret van het Cloud project
- Regio instellen die overeenkomt met je Tuya account (EU/US/CN/IN)

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

### Stap 1 — Tuya IoT Platform

1. Ga naar [iot.tuya.com](https://iot.tuya.com/) en log in
2. Maak een **Cloud project** aan (type: Smart Home)
3. Kopieer je **Client ID** (API Key) en **Client Secret** (API Secret)
4. Koppel je SmartLife/Tuya app-account aan het project via **Link App Account**
5. Stel de juiste regio in (EU = Europa, US = Amerika, etc.)

### Stap 2 — HA integratie

| Veld | Beschrijving |
|------|-------------|
| API Key | Client ID van je Tuya Cloud project |
| API Secret | Client Secret van je Tuya Cloud project |
| Regio | Regio van je Tuya account |
| SmartLife gebruikersnaam | Optioneel, voor extra authenticatie |
| SmartLife wachtwoord | Optioneel |
| Landcode | Landcode zonder +, bijv. `31` voor Nederland |

### Opties (aanpasbaar na installatie)

| Optie | Standaard | Beschrijving |
|-------|-----------|-------------|
| Polling interval | 30 sec | Hoe vaak de status wordt ververst |
| Subnet | 192.168.1.0/24 | Netwerk voor lokale apparaten |
| Scan timeout | 6 sec | Timeout per apparaat bij lokale scan |

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
