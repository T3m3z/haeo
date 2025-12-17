"""Tests for network connectivity helpers."""

from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.const import (
    CONF_ELEMENT_TYPE,
    CONF_NAME,
    CONF_TIER_1_COUNT,
    CONF_TIER_1_DURATION,
    CONF_TIER_2_COUNT,
    CONF_TIER_2_DURATION,
    CONF_TIER_3_COUNT,
    CONF_TIER_3_DURATION,
    CONF_TIER_4_COUNT,
    CONF_TIER_4_DURATION,
    DOMAIN,
)
from custom_components.haeo.elements import ELEMENT_TYPE_GRID, ELEMENT_TYPE_LOAD
from custom_components.haeo.elements.grid import CONF_CONNECTION, CONF_EXPORT_PRICE, CONF_IMPORT_PRICE
from custom_components.haeo.elements.load import CONF_FORECAST
from custom_components.haeo.network import evaluate_network_connectivity


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a configured HAEO hub entry for network tests."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Test Hub",
            CONF_TIER_1_COUNT: 2,
            CONF_TIER_1_DURATION: 30,
            CONF_TIER_2_COUNT: 0,
            CONF_TIER_2_DURATION: 60,
            CONF_TIER_3_COUNT: 0,
            CONF_TIER_3_DURATION: 30,
            CONF_TIER_4_COUNT: 0,
            CONF_TIER_4_DURATION: 60,
        },
        entry_id="test_entry",
        title="Test Hub",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def setup_sensors(hass: HomeAssistant) -> None:
    """Set up mock sensors with forecast data for tests."""
    hass.states.async_set(
        "sensor.import_price",
        "0.30",
        {"forecast": [{"start_time": "2025-01-01T00:00:00+00:00", "price": 0.30}]},
    )
    hass.states.async_set(
        "sensor.export_price",
        "0.10",
        {"forecast": [{"start_time": "2025-01-01T00:00:00+00:00", "price": 0.10}]},
    )
    hass.states.async_set(
        "sensor.load_forecast",
        "1.0",
        {"forecast": [{"start_time": "2025-01-01T00:00:00+00:00", "pv_estimate": 1.0}]},
    )


async def test_evaluate_network_connectivity_connected(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    setup_sensors: None,
) -> None:
    """Network with a grid connected to network should be considered connected."""

    grid = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                CONF_NAME: "Grid",
                CONF_CONNECTION: "network",
                CONF_IMPORT_PRICE: ["sensor.import_price"],
                CONF_EXPORT_PRICE: ["sensor.export_price"],
            }
        ),
        subentry_type=ELEMENT_TYPE_GRID,
        title="Grid",
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(config_entry, grid)

    await evaluate_network_connectivity(hass, config_entry)

    issue_id = f"disconnected_network_{config_entry.entry_id}"
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is None


async def test_evaluate_network_connectivity_disconnected(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    setup_sensors: None,
) -> None:
    """Network with isolated elements should create a repair issue."""

    # Grid connected to "network"
    grid = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                CONF_NAME: "Grid",
                CONF_CONNECTION: "network",
                CONF_IMPORT_PRICE: ["sensor.import_price"],
                CONF_EXPORT_PRICE: ["sensor.export_price"],
            }
        ),
        subentry_type=ELEMENT_TYPE_GRID,
        title="Grid",
        unique_id=None,
    )
    # Load connected to a different node that doesn't exist in the network
    load = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD,
                CONF_NAME: "Load",
                CONF_CONNECTION: "isolated_node",  # Not connected to network
                CONF_FORECAST: ["sensor.load_forecast"],
            }
        ),
        subentry_type=ELEMENT_TYPE_LOAD,
        title="Load",
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(config_entry, grid)
    hass.config_entries.async_add_subentry(config_entry, load)

    await evaluate_network_connectivity(hass, config_entry)

    issue_id = f"disconnected_network_{config_entry.entry_id}"
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "disconnected_network"


async def test_evaluate_network_connectivity_resolves_issue(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    setup_sensors: None,
) -> None:
    """Validation should clear the issue when connectivity is restored."""

    # Grid connected to "network"
    grid = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                CONF_NAME: "Grid",
                CONF_CONNECTION: "network",
                CONF_IMPORT_PRICE: ["sensor.import_price"],
                CONF_EXPORT_PRICE: ["sensor.export_price"],
            }
        ),
        subentry_type=ELEMENT_TYPE_GRID,
        title="Grid",
        unique_id=None,
    )
    # Load initially connected to isolated node
    load = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD,
                CONF_NAME: "Load",
                CONF_CONNECTION: "isolated_node",  # Not connected to network
                CONF_FORECAST: ["sensor.load_forecast"],
            }
        ),
        subentry_type=ELEMENT_TYPE_LOAD,
        title="Load",
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(config_entry, grid)
    hass.config_entries.async_add_subentry(config_entry, load)

    await evaluate_network_connectivity(hass, config_entry)

    # Verify issue was created
    issue_id = f"disconnected_network_{config_entry.entry_id}"
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None

    # Now update load to connect to network
    hass.config_entries.async_remove_subentry(config_entry, load.subentry_id)
    load_fixed = ConfigSubentry(
        data=MappingProxyType(
            {
                CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD,
                CONF_NAME: "Load",
                CONF_CONNECTION: "network",  # Now connected to network
                CONF_FORECAST: ["sensor.load_forecast"],
            }
        ),
        subentry_type=ELEMENT_TYPE_LOAD,
        title="Load",
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(config_entry, load_fixed)

    await evaluate_network_connectivity(hass, config_entry)

    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is None
