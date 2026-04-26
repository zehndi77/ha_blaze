"""Number entities for Blaze amplifier zone gain control."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import GAIN_MIN, GAIN_MAX, GAIN_STEP
from .coordinator import BlazeCoordinator
from .entity import BlazeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        BlazeZoneGain(coordinator, entry, zone) for zone in coordinator.zones
    )


class BlazeZoneGain(BlazeBaseEntity, NumberEntity):
    """Volume/gain control for a single zone."""

    _attr_native_min_value = GAIN_MIN
    _attr_native_max_value = GAIN_MAX
    _attr_native_step = GAIN_STEP
    _attr_native_unit_of_measurement = "dB"

    def __init__(
        self,
        coordinator: BlazeCoordinator,
        entry: ConfigEntry,
        zone: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone{zone}_gain"
        self._attr_name = f"Zone {zone} Gain"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data[self._zone]["gain"]

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.set_gain(self._zone, value)
        await self.coordinator.async_request_refresh()
