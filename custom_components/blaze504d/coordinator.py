"""DataUpdateCoordinator for Blaze Pascal series amplifiers."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .blaze_client import BlazeClient, BlazeConnectionError, BlazeProtocolError
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SIGNAL_SCAN_INTERVAL

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
                prev = (self.data or {}).get(zone, {})
                try:
                    gain = await self.client.get_gain(zone)
                except (BlazeConnectionError, BlazeProtocolError):
                    gain = prev.get("gain", 0.0)
                    _LOGGER.debug("Gain query failed for zone %s, using cached %.1f", zone, gain)
                try:
                    muted = await self.client.get_mute(zone)
                except (BlazeConnectionError, BlazeProtocolError):
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


class BlazeSignalCoordinator(DataUpdateCoordinator[dict]):
    """Polls input and output signal levels at a slow interval (disabled-by-default entities)."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BlazeClient,
        input_ids: list[int],
        output_ids: list[int],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Blaze Signal",
            update_interval=timedelta(seconds=DEFAULT_SIGNAL_SCAN_INTERVAL),
        )
        self.client = client
        self.input_ids = input_ids
        self.output_ids = output_ids

    async def _async_update_data(self) -> dict:
        """Fetch DYN.SIGNAL for all inputs and outputs; cache on per-item failure."""
        prev = self.data or {}
        prev_inputs = prev.get("inputs", {})
        prev_outputs = prev.get("outputs", {})

        inputs: dict[int, float | None] = {}
        for iid in self.input_ids:
            try:
                inputs[iid] = await self.client.get_input_signal(iid)
            except (BlazeConnectionError, BlazeProtocolError):
                inputs[iid] = prev_inputs.get(iid)
                _LOGGER.debug("Input %d signal query failed, using cached", iid)

        outputs: dict[int, float | None] = {}
        for oid in self.output_ids:
            try:
                outputs[oid] = await self.client.get_output_signal(oid)
            except (BlazeConnectionError, BlazeProtocolError):
                outputs[oid] = prev_outputs.get(oid)
                _LOGGER.debug("Output %d signal query failed, using cached", oid)

        return {"inputs": inputs, "outputs": outputs}
