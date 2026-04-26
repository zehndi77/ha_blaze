"""Shared base entity for all Blaze amplifier entities."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST, CONF_NAME, CONF_MODEL_NAME, CONF_SERIAL, CONF_FIRMWARE


class BlazeBaseEntity(CoordinatorEntity):
    """Base entity wiring DeviceInfo from the config entry."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_NAME, entry.data[CONF_HOST]),
            manufacturer="Blaze",
            model=entry.data.get(CONF_MODEL_NAME, "PowerZone Connect"),
            sw_version=entry.data.get(CONF_FIRMWARE),
            serial_number=entry.data.get(CONF_SERIAL),
        )
