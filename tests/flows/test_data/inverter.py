"""Test data and validation for inverter flow configuration."""

from custom_components.haeo.const import CONF_NAME
from custom_components.haeo.elements.inverter import (
    CONF_CONNECTION,
    CONF_EFFICIENCY_EXPORT,
    CONF_EFFICIENCY_IMPORT,
    CONF_MAX_POWER_EXPORT,
    CONF_MAX_POWER_IMPORT,
)

# Test data for inverter flow
VALID_DATA = [
    {
        "description": "Basic inverter configuration",
        "config": {
            CONF_NAME: "Test Inverter",
            CONF_CONNECTION: "network",
            CONF_MAX_POWER_EXPORT: ["sensor.max_power"],
            CONF_MAX_POWER_IMPORT: ["sensor.max_power"],
        },
    },
    {
        "description": "Inverter with efficiency",
        "config": {
            CONF_NAME: "Efficient Inverter",
            CONF_CONNECTION: "network",
            CONF_MAX_POWER_EXPORT: ["sensor.max_power_export"],
            CONF_MAX_POWER_IMPORT: ["sensor.max_power_import"],
            CONF_EFFICIENCY_EXPORT: 97.0,
            CONF_EFFICIENCY_IMPORT: 96.0,
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {
            CONF_NAME: "",
            CONF_CONNECTION: "network",
            CONF_MAX_POWER_EXPORT: ["sensor.max_power"],
        },
        "error": "cannot be empty",
    },
]
