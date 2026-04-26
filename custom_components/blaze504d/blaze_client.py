"""WebSocket client for Blaze PowerZone Connect 504D."""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import ZONES, WS_TIMEOUT, WS_PATH

_LOGGER = logging.getLogger(__name__)


class BlazeConnectionError(Exception):
    """Raised when the WebSocket connection fails."""


class BlazeProtocolError(Exception):
    """Raised when a response cannot be parsed."""


class BlazeClient:
    """Manages a WebSocket connection to a single Blaze 504D amplifier."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._host = host
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._lock = asyncio.Lock()

    @property
    def _url(self) -> str:
        return f"ws://{self._host}{WS_PATH}"

    async def _connect(self) -> None:
        """Open (or reopen) the WebSocket connection."""
        try:
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(self._url),
                timeout=WS_TIMEOUT,
            )
        except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as err:
            raise BlazeConnectionError(f"Cannot connect to {self._url}: {err}") from err

    async def _ensure_connected(self) -> None:
        if self._ws is None or self._ws.closed:
            await self._connect()

    async def _send_recv(self, command: str) -> str:
        """Send a command and return the value response line (starts with '+')."""
        await self._ensure_connected()
        assert self._ws is not None
        try:
            await self._ws.send_str(command)
            async with asyncio.timeout(WS_TIMEOUT):
                while True:
                    msg = await self._ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        line = msg.data.strip()
                        if line.startswith("+"):
                            return line
                        # device echoes the command back prefixed with '*'; skip it
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        self._ws = None
                        raise BlazeConnectionError("WebSocket closed unexpectedly")
        except asyncio.TimeoutError as err:
            self._ws = None
            raise BlazeConnectionError(f"Timeout waiting for response to '{command}'") from err
        except aiohttp.ClientError as err:
            self._ws = None
            raise BlazeConnectionError(f"WebSocket error: {err}") from err

    @staticmethod
    def _parse_float_response(response: str) -> float:
        """Parse '+Zone-A.GAIN -10.00' → -10.0."""
        try:
            return float(response.rsplit(" ", 1)[-1])
        except (ValueError, IndexError) as err:
            raise BlazeProtocolError(f"Cannot parse response: {response!r}") from err

    @staticmethod
    def _parse_bool_response(response: str) -> bool:
        """Parse '+Zone-A.MUTE ON' → True."""
        token = response.rsplit(" ", 1)[-1].upper()
        if token in ("ON", "1", "TRUE"):
            return True
        if token in ("OFF", "0", "FALSE"):
            return False
        raise BlazeProtocolError(f"Cannot parse mute response: {response!r}")

    def _zone_tag(self, zone: str) -> str:
        if zone not in ZONES:
            raise ValueError(f"Zone must be one of {ZONES}, got {zone!r}")
        return f"ZONE-{zone}"

    async def get_gain(self, zone: str) -> float:
        """Return current gain in dB for the given zone."""
        async with self._lock:
            resp = await self._send_recv(f"GET {self._zone_tag(zone)}.GAIN")
        return self._parse_float_response(resp)

    async def set_gain(self, zone: str, db: float) -> float:
        """Set absolute gain in dB. Returns confirmed value."""
        async with self._lock:
            resp = await self._send_recv(f"SET {self._zone_tag(zone)}.GAIN {db:.2f}")
        return self._parse_float_response(resp)

    async def inc_gain(self, zone: str, delta: float) -> float:
        """Increment gain by delta dB. Returns new absolute value."""
        async with self._lock:
            resp = await self._send_recv(f"INC {self._zone_tag(zone)}.GAIN {delta:.2f}")
        return self._parse_float_response(resp)

    async def get_mute(self, zone: str) -> bool:
        """Return mute state for the given zone."""
        async with self._lock:
            resp = await self._send_recv(f"GET {self._zone_tag(zone)}.MUTE")
        return self._parse_bool_response(resp)

    async def set_mute(self, zone: str, muted: bool) -> None:
        """Set mute state for the given zone."""
        value = "ON" if muted else "OFF"
        async with self._lock:
            await self._send_recv(f"SET {self._zone_tag(zone)}.MUTE {value}")

    async def set_all_mute(self, muted: bool) -> None:
        """Mute or unmute all zones sequentially."""
        for zone in ZONES:
            await self.set_mute(zone, muted)

    async def validate_connection(self) -> bool:
        """Test connectivity by querying Zone A gain. Returns True on success."""
        try:
            await self.get_gain("A")
            return True
        except (BlazeConnectionError, BlazeProtocolError):
            return False

    async def close(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
