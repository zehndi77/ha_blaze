"""Sensor entities for Blaze amplifier system state and I/O signal levels."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BlazeCoordinator, BlazeSignalCoordinator
from .entity import BlazeBaseEntity


def _input_label(iid: int) -> str:
    if 100 <= iid <= 107:
        return f"Input {iid - 99} Signal"
    if iid == 200:
        return "SPDIF L Signal"
    if iid == 201:
        return "SPDIF R Signal"
    if 300 <= iid <= 303:
        return f"Dante {iid - 299} Signal"
    return f"Input {iid} Signal"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    entities: list = [BlazeSystemState(runtime.coordinator, entry)]

    sig: BlazeSignalCoordinator = runtime.signal_coordinator
    entities += [BlazeInputSignal(sig, entry, iid) for iid in sig.input_ids]
    entities += [BlazeOutputSignal(sig, entry, oid) for oid in sig.output_ids]

    async_add_entities(entities)


class BlazeSystemState(BlazeBaseEntity, SensorEntity):
    """Sensor reporting SYSTEM.STATUS.STATE: INIT | STANDBY | ON | FAULT."""

    def __init__(self, coordinator: BlazeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_system_state"
        self._attr_name = "System State"
        self._attr_icon = "mdi:amplifier"

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("state")


class BlazeInputSignal(BlazeBaseEntity, SensorEntity):
    """Signal level (dB) for one analog input — disabled by default."""

    _attr_entity_registry_enabled_default = False
    _attr_native_unit_of_measurement = "dB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:signal"

    def __init__(self, coordinator: BlazeSignalCoordinator, entry: ConfigEntry, iid: int) -> None:
        super().__init__(coordinator, entry)
        self._iid = iid
        self._attr_unique_id = f"{entry.entry_id}_input{iid}_signal"
        self._attr_name = _input_label(iid)

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("inputs", {}).get(self._iid)


class BlazeOutputSignal(BlazeBaseEntity, SensorEntity):
    """Signal level (dB) for one output — disabled by default."""

    _attr_entity_registry_enabled_default = False
    _attr_native_unit_of_measurement = "dB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:signal"

    def __init__(self, coordinator: BlazeSignalCoordinator, entry: ConfigEntry, oid: int) -> None:
        super().__init__(coordinator, entry)
        self._oid = oid
        self._attr_unique_id = f"{entry.entry_id}_output{oid}_signal"
        self._attr_name = f"Output {oid} Signal"

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("outputs", {}).get(self._oid)
