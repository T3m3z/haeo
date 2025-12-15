"""Inverter element configuration for HAEO integration.

An Inverter models a DC bus coupled to an AC connection. This replaces
the need for manual node/connection configuration for inverters by
providing a high-level device that creates both the DC bus (as a SourceSink)
and the inverter connection to the AC network.
"""

from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Final, Literal, NotRequired, TypedDict

from custom_components.haeo.model import ModelOutputName
from custom_components.haeo.model.connection import (
    CONNECTION_POWER_MAX_SOURCE_TARGET,
    CONNECTION_POWER_MAX_TARGET_SOURCE,
    CONNECTION_POWER_SOURCE_TARGET,
    CONNECTION_POWER_TARGET_SOURCE,
    CONNECTION_SHADOW_POWER_MAX_SOURCE_TARGET,
    CONNECTION_SHADOW_POWER_MAX_TARGET_SOURCE,
)
from custom_components.haeo.model.const import OUTPUT_TYPE_POWER, OUTPUT_TYPE_POWER_FLOW
from custom_components.haeo.model.output_data import OutputData
from custom_components.haeo.model.source_sink import SOURCE_SINK_POWER_BALANCE
from custom_components.haeo.schema.fields import (
    ElementNameFieldData,
    ElementNameFieldSchema,
    NameFieldData,
    NameFieldSchema,
    PercentageFieldData,
    PercentageFieldSchema,
    PowerSensorFieldData,
    PowerSensorFieldSchema,
)

ELEMENT_TYPE: Final = "inverter"

# Configuration field names
CONF_CONNECTION: Final = "connection"
CONF_MAX_POWER_EXPORT: Final = "max_power_export"
CONF_MAX_POWER_IMPORT: Final = "max_power_import"
CONF_EFFICIENCY_EXPORT: Final = "efficiency_export"
CONF_EFFICIENCY_IMPORT: Final = "efficiency_import"

type InverterOutputName = Literal[
    "inverter_power_export",
    "inverter_power_import",
    "inverter_power_active",
    "inverter_power_max_export",
    "inverter_power_max_import",
    "inverter_power_max_export_price",
    "inverter_power_max_import_price",
    "inverter_dc_bus_power_balance",
]

INVERTER_OUTPUT_NAMES: Final[frozenset[InverterOutputName]] = frozenset(
    (
        INVERTER_POWER_EXPORT := "inverter_power_export",
        INVERTER_POWER_IMPORT := "inverter_power_import",
        INVERTER_POWER_ACTIVE := "inverter_power_active",
        INVERTER_POWER_MAX_EXPORT := "inverter_power_max_export",
        INVERTER_POWER_MAX_IMPORT := "inverter_power_max_import",
        # Shadow prices
        INVERTER_POWER_MAX_EXPORT_PRICE := "inverter_power_max_export_price",
        INVERTER_POWER_MAX_IMPORT_PRICE := "inverter_power_max_import_price",
        # DC bus
        INVERTER_DC_BUS_POWER_BALANCE := "inverter_dc_bus_power_balance",
    )
)

type InverterDeviceName = Literal["inverter"]

INVERTER_DEVICE_NAMES: Final[frozenset[InverterDeviceName]] = frozenset(
    (INVERTER_DEVICE := ELEMENT_TYPE,),
)


class InverterConfigSchema(TypedDict):
    """Inverter element configuration."""

    element_type: Literal["inverter"]
    name: NameFieldSchema
    connection: ElementNameFieldSchema  # AC connection target (typically "network")

    # Optional fields
    max_power_export: NotRequired[PowerSensorFieldSchema]  # DC to AC (export to grid)
    max_power_import: NotRequired[PowerSensorFieldSchema]  # AC to DC (import from grid)
    efficiency_export: NotRequired[PercentageFieldSchema]  # DC to AC efficiency
    efficiency_import: NotRequired[PercentageFieldSchema]  # AC to DC efficiency


class InverterConfigData(TypedDict):
    """Inverter element configuration."""

    element_type: Literal["inverter"]
    name: NameFieldData
    connection: ElementNameFieldData  # AC connection target (typically "network")

    # Optional fields
    max_power_export: NotRequired[PowerSensorFieldData]  # DC to AC (export to grid)
    max_power_import: NotRequired[PowerSensorFieldData]  # AC to DC (import from grid)
    efficiency_export: NotRequired[PercentageFieldData]  # DC to AC efficiency
    efficiency_import: NotRequired[PercentageFieldData]  # AC to DC efficiency


CONFIG_DEFAULTS: dict[str, Any] = {}


def create_model_elements(config: InverterConfigData) -> list[dict[str, Any]]:
    """Create model elements for Inverter configuration.

    Creates:
    - A SourceSink node named `{name}` representing the DC bus
    - A Connection from `{name}` to `{connection}` representing the inverter
    """
    return [
        # DC bus as a SourceSink (junction point, neither source nor sink)
        {"element_type": "source_sink", "name": config["name"], "is_source": False, "is_sink": False},
        # Inverter connection from DC bus to AC target
        {
            "element_type": "connection",
            "name": f"{config['name']}:connection",
            "source": config["name"],
            "target": config["connection"],
            # source_target = DC to AC = EXPORT
            "max_power_source_target": config.get("max_power_export"),
            "efficiency_source_target": config.get("efficiency_export"),
            # target_source = AC to DC = IMPORT
            "max_power_target_source": config.get("max_power_import"),
            "efficiency_target_source": config.get("efficiency_import"),
        },
    ]


def outputs(
    name: str, model_outputs: Mapping[str, Mapping[ModelOutputName, OutputData]], _config: InverterConfigData
) -> Mapping[InverterDeviceName, Mapping[InverterOutputName, OutputData]]:
    """Map model outputs to inverter-specific output names."""

    dc_bus = model_outputs[name]
    connection = model_outputs[f"{name}:connection"]

    inverter_outputs: dict[InverterOutputName, OutputData] = {}

    # DC bus power balance (shadow price)
    inverter_outputs[INVERTER_DC_BUS_POWER_BALANCE] = dc_bus[SOURCE_SINK_POWER_BALANCE]

    # source_target = DC to AC = EXPORT
    # target_source = AC to DC = IMPORT
    inverter_outputs[INVERTER_POWER_EXPORT] = replace(
        connection[CONNECTION_POWER_SOURCE_TARGET], type=OUTPUT_TYPE_POWER
    )
    inverter_outputs[INVERTER_POWER_IMPORT] = replace(
        connection[CONNECTION_POWER_TARGET_SOURCE], type=OUTPUT_TYPE_POWER
    )

    # Active power (export - import, positive = exporting to AC)
    inverter_outputs[INVERTER_POWER_ACTIVE] = replace(
        connection[CONNECTION_POWER_SOURCE_TARGET],
        values=[
            exp - imp
            for exp, imp in zip(
                connection[CONNECTION_POWER_SOURCE_TARGET].values,
                connection[CONNECTION_POWER_TARGET_SOURCE].values,
                strict=True,
            )
        ],
        direction=None,
        type=OUTPUT_TYPE_POWER_FLOW,
    )

    # Optional outputs (only present if configured)
    if CONNECTION_POWER_MAX_SOURCE_TARGET in connection:
        inverter_outputs[INVERTER_POWER_MAX_EXPORT] = connection[CONNECTION_POWER_MAX_SOURCE_TARGET]
        inverter_outputs[INVERTER_POWER_MAX_EXPORT_PRICE] = connection[CONNECTION_SHADOW_POWER_MAX_SOURCE_TARGET]

    if CONNECTION_POWER_MAX_TARGET_SOURCE in connection:
        inverter_outputs[INVERTER_POWER_MAX_IMPORT] = connection[CONNECTION_POWER_MAX_TARGET_SOURCE]
        inverter_outputs[INVERTER_POWER_MAX_IMPORT_PRICE] = connection[CONNECTION_SHADOW_POWER_MAX_TARGET_SOURCE]

    return {INVERTER_DEVICE: inverter_outputs}


__all__ = [
    "CONF_CONNECTION",
    "CONF_EFFICIENCY_EXPORT",
    "CONF_EFFICIENCY_IMPORT",
    "CONF_MAX_POWER_EXPORT",
    "CONF_MAX_POWER_IMPORT",
    "ELEMENT_TYPE",
    "INVERTER_DC_BUS_POWER_BALANCE",
    "INVERTER_DEVICE_NAMES",
    "INVERTER_OUTPUT_NAMES",
    "INVERTER_POWER_ACTIVE",
    "INVERTER_POWER_EXPORT",
    "INVERTER_POWER_IMPORT",
    "INVERTER_POWER_MAX_EXPORT",
    "INVERTER_POWER_MAX_EXPORT_PRICE",
    "INVERTER_POWER_MAX_IMPORT",
    "INVERTER_POWER_MAX_IMPORT_PRICE",
    "CONFIG_DEFAULTS",
    "InverterConfigData",
    "InverterConfigSchema",
    "InverterOutputName",
    "create_model_elements",
    "outputs",
]
