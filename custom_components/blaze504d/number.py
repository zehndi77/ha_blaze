"""Number entities for Blaze 504D zone gain control."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ZONES, GAIN_MIN, GAIN_MAX, GAIN_STEP, CONF_HOST
from .coordinator import BlazeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data
    async_add_entities(
        BlazeZoneGain(coordinator, entry, zone) for zone in ZONES
    )


class BlazeZoneGain(CoordinatorEntity[BlazeCoordinator], NumberEntity):
    """Volume/gain control for a single zone."""

    _attr_mode = NumberMode.SLIDER
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
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone{zone}_gain"
        self._attr_name = f"Zone {zone} Gain"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name", entry.data[CONF_HOST]),
            manufacturer="Blaze",
            model="PowerZone Connect 504D",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._zone, {}).get("gain")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.set_gain(self._zone, value)
        await self.coordinator.async_request_refresh()
