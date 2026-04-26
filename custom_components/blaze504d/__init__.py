"""Blaze Pascal series amplifier integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .blaze_client import BlazeClient, BlazeConnectionError, BlazeProtocolError
from .coordinator import BlazeCoordinator, BlazeSignalCoordinator
from .const import (
    DOMAIN, PLATFORMS, CONF_HOST, CONF_ZONE_COUNT,
    DEFAULT_ZONE_COUNT, ZONE_LETTERS_BY_COUNT,
    ANALOG_INPUT_BASE_ID, OUTPUT_BASE_ID,
    SPDIF_INPUT_IDS, DANTE_INPUT_IDS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class BlazeRuntimeData:
    coordinator: BlazeCoordinator
    signal_coordinator: BlazeSignalCoordinator


type BlazeConfigEntry = ConfigEntry[BlazeRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: BlazeConfigEntry) -> bool:
    """Set up Blaze amplifier from a config entry."""
    session = async_get_clientsession(hass)
    client = BlazeClient(session, entry.data[CONF_HOST])

    zone_count = entry.data.get(CONF_ZONE_COUNT, DEFAULT_ZONE_COUNT)
    zones = ZONE_LETTERS_BY_COUNT.get(zone_count, ZONE_LETTERS_BY_COUNT[DEFAULT_ZONE_COUNT])

    coordinator = BlazeCoordinator(hass, client, zones)
    await coordinator.async_config_entry_first_refresh()

    # Query I/O counts independently; fall back to zone_count if unavailable
    try:
        input_count = await client.get_input_count()
        output_count = await client.get_output_count()
    except (BlazeConnectionError, BlazeProtocolError):
        _LOGGER.warning("Could not query I/O counts from %s; defaulting to zone count (%d)", entry.data[CONF_HOST], zone_count)
        input_count = zone_count
        output_count = zone_count

    input_ids = (
        [ANALOG_INPUT_BASE_ID + i for i in range(input_count)]
        + SPDIF_INPUT_IDS
        + DANTE_INPUT_IDS
    )
    output_ids = list(range(OUTPUT_BASE_ID, OUTPUT_BASE_ID + output_count))
    signal_coordinator = BlazeSignalCoordinator(hass, client, input_ids, output_ids)

    entry.runtime_data = BlazeRuntimeData(
        coordinator=coordinator,
        signal_coordinator=signal_coordinator,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlazeConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.coordinator.client.close()
    return unloaded
