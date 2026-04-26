"""Sensor entities for Blaze amplifier system state."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BlazeCoordinator
from .entity import BlazeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data
    async_add_entities([BlazeSystemState(coordinator, entry)])


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
