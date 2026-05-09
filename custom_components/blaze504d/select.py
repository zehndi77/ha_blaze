"""Select entities for Blaze amplifier — zone input source routing."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_SOURCE_MAP, INPUT_SOURCE_ID_BY_NAME
from .coordinator import BlazeCoordinator
from .entity import BlazeBaseEntity

_SOURCE_OPTIONS = list(INPUT_SOURCE_MAP.values())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BlazeCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        cls(coordinator, entry, zone)
        for cls in (BlazeZonePrimarySrc, BlazeZonePrioritySrc)
        for zone in coordinator.zones
    )


class _BlazeZoneSrcBase(BlazeBaseEntity, SelectEntity):
    """Shared base for per-zone input source select entities."""

    _attr_options = _SOURCE_OPTIONS
    _attr_icon = "mdi:import"
    _data_key: str
    _display_label: str

    def __init__(
        self,
        coordinator: BlazeCoordinator,
        entry: ConfigEntry,
        zone: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone{zone}_{self._data_key}"
        self._attr_name = f"Zone {zone} {self._display_label}"

    @property
    def current_option(self) -> str | None:
        src_id = (self.coordinator.data or {}).get(self._zone, {}).get(self._data_key)
        return INPUT_SOURCE_MAP.get(src_id)


class BlazeZonePrimarySrc(_BlazeZoneSrcBase):
    """Input source selector for ZONE-{ZID}.PRIMARY_SRC."""

    _data_key = "primary_src"
    _display_label = "Primary Source"

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_primary_src(self._zone, INPUT_SOURCE_ID_BY_NAME[option])
        await self.coordinator.async_request_refresh()


class BlazeZonePrioritySrc(_BlazeZoneSrcBase):
    """Input source selector for ZONE-{ZID}.PRIORITY_SRC."""

    _data_key = "priority_src"
    _display_label = "Priority Source"

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.set_priority_src(self._zone, INPUT_SOURCE_ID_BY_NAME[option])
        await self.coordinator.async_request_refresh()
