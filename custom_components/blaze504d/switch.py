"""Switch entities for Blaze 504D zone mute control."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ZONES, CONF_HOST
from .coordinator import BlazeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data
    entities: list[SwitchEntity] = [
        BlazeZoneMute(coordinator, entry, zone) for zone in ZONES
    ]
    entities.append(BlazeAllMute(coordinator, entry))
    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get("name", entry.data[CONF_HOST]),
        manufacturer="Blaze",
        model="PowerZone Connect 504D",
    )


class BlazeZoneMute(CoordinatorEntity[BlazeCoordinator], SwitchEntity):
    """Mute switch for a single zone."""

    def __init__(
        self,
        coordinator: BlazeCoordinator,
        entry: ConfigEntry,
        zone: str,
    ) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone{zone}_mute"
        self._attr_name = f"Zone {zone} Mute"
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._zone, {}).get("muted")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_mute(self._zone, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_mute(self._zone, False)
        await self.coordinator.async_request_refresh()


class BlazeAllMute(CoordinatorEntity[BlazeCoordinator], SwitchEntity):
    """Master mute — on only when ALL zones are muted."""

    def __init__(self, coordinator: BlazeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_all_mute"
        self._attr_name = "All Zones Mute"
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return all(
            self.coordinator.data.get(z, {}).get("muted", False) for z in ZONES
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.set_all_mute(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.set_all_mute(False)
        await self.coordinator.async_request_refresh()
