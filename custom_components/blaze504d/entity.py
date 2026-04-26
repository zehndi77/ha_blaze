"""Shared base entity for all Blaze 504D entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST
from .coordinator import BlazeCoordinator


class BlazeBaseEntity(CoordinatorEntity[BlazeCoordinator]):
    """Base entity that wires DeviceInfo from the config entry."""

    def __init__(self, coordinator: BlazeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name", entry.data[CONF_HOST]),
            manufacturer="Blaze",
            model="PowerZone Connect 504D",
        )
