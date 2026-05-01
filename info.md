# VUN Tuya

Lokale Tuya-integratie voor Home Assistant. Bestuurt apparaten rechtstreeks via het lokale netwerk met automatische Tuya Cloud sync voor local keys.

## Functies

- Lokale LAN-besturing — geen Cloud latency bij gebruik
- Automatische Cloud sync voor apparaatlijst en local keys
- Cloud fallback als lokale verbinding mislukt
- Ondersteunde platforms: licht, schakelaar, klimaat, sensor, binaire sensor, ventilator
- Energie-meting voor slimme stekkers (vermogen, stroom, spanning)
- Eenvoudige installatie via de Home Assistant UI

## Configuratie vereisten

- Tuya IoT Platform account met een gekoppeld Cloud project
- API Key en API Secret van het Cloud project
- Regio die overeenkomt met je Tuya account (EU/US/CN/IN)

Zie de [volledige documentatie](https://github.com/vincentvunen/vun-tuya-hacs) voor installatie-instructies.
