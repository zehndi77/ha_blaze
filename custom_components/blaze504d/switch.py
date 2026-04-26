"""Switch entities for Blaze 504D zone mute control."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ZONES
from .coordinator import BlazeCoordinator
from .entity import BlazeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data
    async_add_entities([
        *[BlazeZoneMute(coordinator, entry, zone) for zone in ZONES],
        BlazeAllMute(coordinator, entry),
    ])


class BlazeZoneMute(BlazeBaseEntity, SwitchEntity):
    """Mute switch for a single zone."""

    def __init__(
        self,
        coordinator: BlazeCoordinator,
        entry: ConfigEntry,
        zone: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone{zone}_mute"
        self._attr_name = f"Zone {zone} Mute"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data[self._zone]["muted"]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_mute(self._zone, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_mute(self._zone, False)
        await self.coordinator.async_request_refresh()


class BlazeAllMute(BlazeBaseEntity, SwitchEntity):
    """Master mute — on only when ALL zones are muted."""

    def __init__(self, coordinator: BlazeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_all_mute"
        self._attr_name = "All Zones Mute"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return all(self.coordinator.data[z]["muted"] for z in ZONES)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_all_mute(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_all_mute(False)
        await self.coordinator.async_request_refresh()
