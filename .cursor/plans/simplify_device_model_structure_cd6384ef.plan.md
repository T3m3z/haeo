---
name: Simplify Device Model Structure
overview: Refactor the device layer to simplify the model by adding a real network element, removing standalone nodes and connections, and introducing a Hybrid Inverter element.
todos:
  - id: 1_add_network_element
    content: Modify network loader to add network source/sink element
    status: pending
  - id: 2_create_hybrid_inverter
    content: Create hybrid_inverter.py with config schema and model generation
    status: pending
  - id: 3_update_elements_registry
    content: Update elements/__init__.py to remove node/connection and add hybrid_inverter
    status: pending
    dependencies:
      - 2_create_hybrid_inverter
  - id: 4_update_validation
    content: Update validation.py to handle removal of connection element type constant
    status: pending
    dependencies:
      - 3_update_elements_registry
  - id: 5_delete_files
    content: Delete node.py and connection.py
    status: pending
    dependencies:
      - 3_update_elements_registry
  - id: 6_update_docs
    content: Update documentation (index.md, hybrid-inverter.md, delete old docs)
    status: pending
    dependencies:
      - 5_delete_files
---

# Simplify Device Model Structure

This plan addresses the user's request to simplify the model structure by making the network a real element, removing low-level Node/Connection device elements, and introducing a Hybrid Inverter element to manage DC/AC coupling.

## 1. Make ELEMENT_TYPE_NETWORK a Real Element

We will modify the network loader to explicitly create a `SourceSink` model element for the network itself. This provides a central connection point (the "grid" or "main bus") for other elements.

-   **File:** [`custom_components/haeo/data/loader/network.py`](custom_components/haeo/data/loader/network.py)
-   **Action:** In `load_network`, add a `SourceSink` element named `ELEMENT_TYPE_NETWORK` (value "network") with `is_source=False` and `is_sink=False`.

## 2. Introduce HybridInverter Element

We will create a new `HybridInverter` device element that models a DC bus coupled to an AC connection. This replaces the need for manual node/connection configuration for hybrid inverters.

-   **File:** Create [`custom_components/haeo/elements/hybrid_inverter.py`](custom_components/haeo/elements/hybrid_inverter.py)
    -   **Config Schema:** `name`, `connection` (target), `max_power_export`, `max_power_import`, `efficiency_export`, `efficiency_import`.
    -   **Model Generation:**
        -   Create a `SourceSink` node named `{name}` (representing the DC bus).
        -   Create a `Connection` from `{name}` to `{connection}` (representing the inverter).
    -   **Outputs:** Map connection outputs to device outputs.

## 3. Remove Node and Connection Device Elements

We will remove the ability to configure raw `Node` and `Connection` elements in the device layer, forcing a more structured approach using defined device types.

-   **File:** [`custom_components/haeo/elements/__init__.py`](custom_components/haeo/elements/__init__.py)
    -   Remove imports and registry entries for `node` and `connection`.
    -   Register `hybrid_inverter` element.
-   **File:** [`custom_components/haeo/validation.py`](custom_components/haeo/validation.py)
    -   Update logic to avoid dependence on removed `ELEMENT_TYPE_CONNECTION` constant from `elements` package.
-   **Files:** Delete [`custom_components/haeo/elements/node.py`](custom_components/haeo/elements/node.py) and [`custom_components/haeo/elements/connection.py`](custom_components/haeo/elements/connection.py).

## 4. Update Documentation

We will update the documentation to reflect these changes.

-   **File:** [`docs/modeling/device-layer/index.md`](docs/modeling/device-layer/index.md)
    -   Remove references to Node and Connection.
    -   Add Hybrid Inverter to the list.
-   **File:** Create [`docs/modeling/device-layer/hybrid-inverter.md`](docs/modeling/device-layer/hybrid-inverter.md)
-   **Files:** Delete [`docs/modeling/device-layer/node.md`](docs/modeling/device-layer/node.md) and [`docs/modeling/device-layer/connection.md`](docs/modeling/device-layer/connection.md).