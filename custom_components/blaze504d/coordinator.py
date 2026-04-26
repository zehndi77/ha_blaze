"""DataUpdateCoordinator for Blaze 504D."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .blaze_client import BlazeClient, BlazeConnectionError
from .const import DEFAULT_SCAN_INTERVAL, ZONES

_LOGGER = logging.getLogger(__name__)


class BlazeCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Polls all zones on a single WebSocket connection."""

    def __init__(self, hass: HomeAssistant, client: BlazeClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Blaze 504D",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch gain and mute state for all zones.

        Returns: {"A": {"gain": -10.0, "muted": False}, ...}
        """
        try:
            data: dict[str, dict] = {}
            for zone in ZONES:
                gain = await self.client.get_gain(zone)
                muted = await self.client.get_mute(zone)
                data[zone] = {"gain": gain, "muted": muted}
            return data
        except BlazeConnectionError as err:
            raise UpdateFailed(f"Error communicating with Blaze 504D: {err}") from err
