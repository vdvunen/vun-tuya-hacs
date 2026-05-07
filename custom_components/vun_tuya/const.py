"""Constanten voor de VUN Tuya integratie."""
from __future__ import annotations

DOMAIN = "vun_tuya"

# Config keys
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_REGION = "region"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_COUNTRY_CODE = "country_code"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SUBNET = "subnet"
CONF_SCAN_TIMEOUT = "scan_timeout"

# Defaults
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SUBNET = "192.168.1.0/24"
DEFAULT_SCAN_TIMEOUT = 6
DEFAULT_COUNTRY_CODE = "31"
DEFAULT_REGION = "eu"

# Tuya API regio's
TUYA_REGIONS = {
    "eu": "Europe (openapi.tuyaeu.com)",
    "us": "US (openapi.tuyaus.com)",
    "cn": "China (openapi.tuyacn.com)",
    "in": "India (openapi.tuyain.com)",
}

TUYA_REGION_URLS = {
    "eu": "https://openapi.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
}

# Platforms die deze integratie aanmaakt
PLATFORMS = [
    "light", "switch", "climate", "sensor", "binary_sensor", "fan",
    "cover", "lock", "vacuum", "alarm_control_panel",
]

# Categorie → primair platform
CATEGORY_PLATFORM_MAP: dict[str, str] = {
    # Verlichting
    "dj": "light",
    "dd": "light",
    "fwd": "light",
    "dc": "light",
    "tgq": "light",
    "xdd": "light",
    # Ventilator
    "fs": "fan",
    "fsd": "fan",
    "fskg": "fan",
    # Schakelaars
    "kg": "switch",
    "tgkg": "switch",
    "cz": "switch",
    "pc": "switch",
    "dlq": "switch",
    # Klimaat
    "kt": "climate",
    "wnykq": "climate",
    "qn": "climate",
    "rs": "climate",
    "wk": "climate",
    "wkf": "climate",
    "zndb": "climate",
    "sfkzq": "climate",
    "dshbj": "climate",
    # Sensoren
    "wsdcg": "sensor",
    "co2bj": "sensor",
    "pm25": "sensor",
    "ldcg": "sensor",
    # Binaire sensoren
    "pir": "binary_sensor",
    "mcs": "binary_sensor",
    "ywbj": "binary_sensor",
    "jwbj": "binary_sensor",
    # Videodeurbel → binary_sensor (bel/beweging)
    "sp": "binary_sensor",
    "dbl": "binary_sensor",
    "sp2": "binary_sensor",
    "ds": "binary_sensor",
    # Rolluiken / gordijnen
    "cl": "cover",
    "clkg": "cover",
    "wkcz": "cover",
    # Sloten
    "ms": "lock",
    "jtmspro": "lock",
    "videolock": "lock",
    # Robotstofzuigers
    "sd": "vacuum",
    "sweeper": "vacuum",
    "mop": "vacuum",
    "sz": "vacuum",
    "sdmop": "vacuum",
    # Alarmpanelen
    "alarm": "alarm_control_panel",
    "wg": "alarm_control_panel",
    "mal": "alarm_control_panel",
}

# DP codes voor lichten
LIGHT_DPS = {
    "switch": ["switch_led", "switch"],
    "brightness": ["bright_value_v2", "bright_value"],
    "color_temp": ["temp_value_v2", "temp_value"],
    "color": ["colour_data_v2", "colour_data"],
    "work_mode": ["work_mode"],
}

# DP codes voor ventilatoren
FAN_DPS = {
    "switch": ["switch_fan", "fan_switch", "switch"],
    "speed_enum": ["fan_speed_enum"],
    "speed_percent": ["fan_speed_percent"],
    "oscillate": ["fan_direction", "oscillate"],
    "light_switch": ["switch_led"],
}

# DP codes voor klimaat (thermostaat / heater / airco)
CLIMATE_DPS = {
    "switch": ["switch", "on_off"],
    "mode": ["mode", "work_mode"],
    "target_temp": ["temp_set", "temp_set_f"],
    "current_temp": ["temp_current", "upper_temp", "va_temperature"],
    "humidity": ["humidity_current", "humidity_set"],
    "preset": ["eco_mode", "level", "child_lock"],
    "fan_speed": ["fan_speed_enum"],
}

# DP codes voor schakelaars (inclusief meervoudig)
SWITCH_DPS = [
    "switch_1", "switch_2", "switch_3", "switch_4",
    "switch_5", "switch_6",
    "switch_usb1", "switch_usb2",
    "switch",
]

# DP codes voor sensoren
SENSOR_DPS: dict[str, dict] = {
    "cur_power": {
        "name": "Vermogen",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement",
        "scale": 0.1,
    },
    "cur_current": {
        "name": "Stroom",
        "unit": "mA",
        "device_class": "current",
        "state_class": "measurement",
        "scale": 1,
    },
    "cur_voltage": {
        "name": "Spanning",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement",
        "scale": 0.1,
    },
    "va_temperature": {
        "name": "Temperatuur",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "scale": 0.1,
    },
    "va_humidity": {
        "name": "Luchtvochtigheid",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "scale": 1,
    },
    "temp_current": {
        "name": "Huidige temperatuur",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "scale": 0.1,
    },
    "humidity_current": {
        "name": "Huidige luchtvochtigheid",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "scale": 1,
    },
    "battery_percentage": {
        "name": "Batterij",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "scale": 1,
    },
    "co2_value": {
        "name": "CO2",
        "unit": "ppm",
        "device_class": "carbon_dioxide",
        "state_class": "measurement",
        "scale": 1,
    },
    "pm25_value": {
        "name": "PM2.5",
        "unit": "µg/m³",
        "device_class": "pm25",
        "state_class": "measurement",
        "scale": 1,
    },
    "energy_today": {
        "name": "Energie vandaag",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "scale": 0.01,
    },
    "energy_total": {
        "name": "Energie totaal",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "scale": 0.01,
    },
}

# DP codes voor binaire sensoren
BINARY_SENSOR_DPS: dict[str, dict] = {
    "pir": {
        "name": "Beweging",
        "device_class": "motion",
        "on_value": "pir",
    },
    "doorcontact_state": {
        "name": "Deur/raam",
        "device_class": "door",
        "on_value": True,
    },
    "smoke_sensor_status": {
        "name": "Rook",
        "device_class": "smoke",
        "on_value": "alarm",
    },
    "gas_sensor_status": {
        "name": "Gas",
        "device_class": "gas",
        "on_value": "alarm",
    },
    "water_sensor": {
        "name": "Waterlek",
        "device_class": "moisture",
        "on_value": "alarm",
    },
    "alarm_lock": {
        "name": "Vergrendeling",
        "device_class": "lock",
        "on_value": True,
    },
    "alarm_temperature": {
        "name": "Temperatuuralarm",
        "device_class": "heat",
        "on_value": True,
    },
    # Videodeurbel
    "doorbell_active": {
        "name": "Deurbel",
        "device_class": "sound",
        "on_value": True,
    },
    "motion_switch": {
        "name": "Beweging",
        "device_class": "motion",
        "on_value": True,
    },
}

# Data opslag keys
DATA_COORDINATOR = "coordinator"
DATA_DEVICES = "devices"
