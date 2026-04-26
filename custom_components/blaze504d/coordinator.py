"""DataUpdateCoordinator for Blaze Pascal series amplifiers."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .blaze_client import BlazeClient, BlazeConnectionError, BlazeProtocolError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BlazeCoordinator(DataUpdateCoordinator[dict]):
    """Polls all zones and system state on a single WebSocket connection."""

    def __init__(
        self, hass: HomeAssistant, client: BlazeClient, zones: list[str]
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Blaze Amplifier",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.zones = zones

    async def _async_update_data(self) -> dict:
        """Fetch gain, mute for all zones and system state.

        Returns dict with zone letters as keys ({"A": {"gain": float, "muted": bool}, ...})
        plus a "state" key (str: INIT|STANDBY|ON|FAULT).
        """
        try:
            data: dict = {}

            for zone in self.zones:
                gain = await self.client.get_gain(zone)
                try:
                    muted = await self.client.get_mute(zone)
                except (BlazeConnectionError, BlazeProtocolError):
                    prev = (self.data or {}).get(zone, {})
                    muted = prev.get("muted", False)
                    _LOGGER.debug("Mute query failed for zone %s, using cached %s", zone, muted)
                data[zone] = {"gain": gain, "muted": muted}

            try:
                data["state"] = await self.client.get_system_state()
            except (BlazeConnectionError, BlazeProtocolError):
                data["state"] = (self.data or {}).get("state", "ON")
                _LOGGER.debug("System state query failed, using cached value")

            return data

        except BlazeConnectionError as err:
            raise UpdateFailed(f"Error communicating with amplifier: {err}") from err
