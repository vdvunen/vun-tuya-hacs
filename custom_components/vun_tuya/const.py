"""Constanten voor de VUN Tuya integratie."""
from __future__ import annotations

DOMAIN = "vun_tuya"

# Config keys
CONF_HOST = "host"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_HOST = "http://192.168.1.100:7654"

# Platforms die deze integratie aanmaakt
PLATFORMS = [
    "light",
    "switch",
    "fan",
    "climate",
    "sensor",
    "cover",
    "lock",
    "binary_sensor",
    "vacuum",
    "alarm_control_panel",
]

# Data opslag keys
DATA_COORDINATOR = "coordinator"
