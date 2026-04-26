"""Blaze PowerZone Connect 504D integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .blaze_client import BlazeClient
from .coordinator import BlazeCoordinator
from .const import DOMAIN, PLATFORMS, CONF_HOST

type BlazeConfigEntry = ConfigEntry[BlazeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BlazeConfigEntry) -> bool:
    """Set up Blaze 504D from a config entry."""
    session = async_get_clientsession(hass)
    client = BlazeClient(session, entry.data[CONF_HOST])
    coordinator = BlazeCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlazeConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.close()
    return unloaded
