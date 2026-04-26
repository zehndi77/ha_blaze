"""WebSocket client for Blaze Pascal series amplifiers."""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import ALL_VALID_ZONES, WS_TIMEOUT, WS_PATH

_LOGGER = logging.getLogger(__name__)


class BlazeConnectionError(Exception):
    """Raised when the WebSocket connection fails."""


class BlazeProtocolError(Exception):
    """Raised when a response cannot be parsed."""


class BlazeClient:
    """Manages a WebSocket connection to a single Blaze Pascal series amplifier."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._host = host
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._lock = asyncio.Lock()

    @property
    def _url(self) -> str:
        return f"ws://{self._host}{WS_PATH}"

    async def _connect(self) -> None:
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

    async def _send_with_retry(self, command: str) -> None:
        """Send command string; reconnect once on transport-close race before raising."""
        for attempt in range(2):
            await self._ensure_connected()
            assert self._ws is not None
            try:
                await self._ws.send_str(command)
                return
            except aiohttp.ClientConnectionResetError:
                self._ws = None
                if attempt == 1:
                    raise BlazeConnectionError(f"Connection reset sending '{command}'")
                _LOGGER.debug("Blaze WS reset during send, reconnecting")
            except aiohttp.ClientError as err:
                self._ws = None
                raise BlazeConnectionError(f"WebSocket error: {err}") from err

    async def _send_recv(self, command: str) -> str:
        """Send a command and return the first '+' value response line."""
        await self._send_with_retry(command)
        assert self._ws is not None
        try:
            async with asyncio.timeout(WS_TIMEOUT):
                while True:
                    msg = await self._ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        for line in msg.data.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("+"):
                                return line
                            if line.startswith("#"):
                                raise BlazeProtocolError(f"Device error: {line!r}")
                            _LOGGER.debug("Blaze WS recv: %r", line)
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        self._ws = None
                        raise BlazeConnectionError("WebSocket closed unexpectedly")
        except asyncio.TimeoutError as err:
            self._ws = None
            raise BlazeConnectionError(f"Timeout waiting for response to '{command}'") from err
        except aiohttp.ClientError as err:
            self._ws = None
            raise BlazeConnectionError(f"WebSocket error: {err}") from err

    async def _send_fire(self, command: str) -> None:
        """Send a command; accept '*' or '+' echo as confirmation (no value response expected)."""
        await self._send_with_retry(command)
        assert self._ws is not None
        try:
            async with asyncio.timeout(WS_TIMEOUT):
                while True:
                    msg = await self._ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        for line in msg.data.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            _LOGGER.debug("Blaze WS recv: %r", line)
                            if line.startswith("+") or line.startswith("*"):
                                return
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        self._ws = None
                        raise BlazeConnectionError("WebSocket closed unexpectedly")
        except asyncio.TimeoutError:
            # Echo not received; command was sent, state confirmed on next poll.
            _LOGGER.warning("No ack for '%s' within %ss; command likely applied", command, WS_TIMEOUT)
            self._ws = None
        except aiohttp.ClientError as err:
            self._ws = None
            raise BlazeConnectionError(f"WebSocket error: {err}") from err

    @staticmethod
    def _parse_float_response(response: str) -> float:
        """Parse '+REGISTER value' → float from last space-separated token."""
        try:
            return float(response.rsplit(" ", 1)[-1])
        except (ValueError, IndexError) as err:
            raise BlazeProtocolError(f"Cannot parse float response: {response!r}") from err

    @staticmethod
    def _parse_str_response(response: str) -> str:
        """Parse '+REGISTER "value"' or '+REGISTER value' → value string."""
        _, _, value = response.partition(" ")
        return value.strip().strip('"')

    @staticmethod
    def _parse_bool_response(response: str) -> bool:
        """Parse '+ZONE-A.MUTE 0' → False (also accepts ON/OFF)."""
        token = response.rsplit(" ", 1)[-1].upper().strip('"')
        if token in ("ON", "1", "TRUE"):
            return True
        if token in ("OFF", "0", "FALSE"):
            return False
        raise BlazeProtocolError(f"Cannot parse bool response: {response!r}")

    def _zone_tag(self, zone: str) -> str:
        if zone not in ALL_VALID_ZONES:
            raise ValueError(f"Zone must be one of {ALL_VALID_ZONES}, got {zone!r}")
        return f"ZONE-{zone}"

    # ── Device info ────────────────────────────────────────────────────────────

    async def get_zone_count(self) -> int:
        async with self._lock:
            resp = await self._send_recv("GET ZONE.COUNT")
        return int(self._parse_float_response(resp))

    async def get_model_name(self) -> str:
        async with self._lock:
            resp = await self._send_recv("GET SYSTEM.DEVICE.MODEL_NAME")
        return self._parse_str_response(resp)

    async def get_serial(self) -> str:
        async with self._lock:
            resp = await self._send_recv("GET SYSTEM.DEVICE.SERIAL")
        return self._parse_str_response(resp)

    async def get_firmware(self) -> str:
        async with self._lock:
            resp = await self._send_recv("GET SYSTEM.DEVICE.FIRMWARE")
        return self._parse_str_response(resp)

    async def get_device_info(self) -> dict:
        """Return zone_count, model_name, serial, firmware from a single connection."""
        return {
            "zone_count": await self.get_zone_count(),
            "model_name": await self.get_model_name(),
            "serial": await self.get_serial(),
            "firmware": await self.get_firmware(),
        }

    async def validate_connection(self) -> bool:
        """Test connectivity. Returns True on success."""
        try:
            await self.get_zone_count()
            return True
        except (BlazeConnectionError, BlazeProtocolError):
            return False

    # ── System status ──────────────────────────────────────────────────────────

    async def get_system_state(self) -> str:
        """Return SYSTEM.STATUS.STATE: INIT | STANDBY | ON | FAULT."""
        async with self._lock:
            resp = await self._send_recv("GET SYSTEM.STATUS.STATE")
        return self._parse_str_response(resp)

    # ── I/O counts and signal levels ──────────────────────────────────────────

    async def get_input_count(self) -> int:
        async with self._lock:
            resp = await self._send_recv("GET IN.COUNT")
        return int(self._parse_float_response(resp))

    async def get_output_count(self) -> int:
        async with self._lock:
            resp = await self._send_recv("GET OUTPUT.COUNT")
        return int(self._parse_float_response(resp))

    async def get_input_signal(self, iid: int) -> float:
        """Return dynamic signal level (dB) for analog input IID (100+)."""
        async with self._lock:
            resp = await self._send_recv(f"GET IN-{iid}.DYN.SIGNAL")
        return self._parse_float_response(resp)

    async def get_output_signal(self, oid: int) -> float:
        """Return dynamic signal level (dB) for output OID (1+)."""
        async with self._lock:
            resp = await self._send_recv(f"GET OUT-{oid}.DYN.SIGNAL")
        return self._parse_float_response(resp)

    # ── Power ──────────────────────────────────────────────────────────────────

    async def power_on(self) -> None:
        async with self._lock:
            await self._send_fire("POWER_ON")

    async def power_off(self) -> None:
        async with self._lock:
            await self._send_fire("POWER_OFF")

    # ── Zone gain ──────────────────────────────────────────────────────────────

    async def get_gain(self, zone: str) -> float:
        """Return current gain in dB via GET (always returns '+' response per API spec)."""
        async with self._lock:
            resp = await self._send_recv(f"GET {self._zone_tag(zone)}.GAIN")
        return self._parse_float_response(resp)

    async def set_gain(self, zone: str, db: float) -> float:
        """Set absolute gain in dB using INC delta (get current first)."""
        current = await self.get_gain(zone)
        delta = round(db - current, 2)
        if abs(delta) < 0.01:
            return current
        return await self.inc_gain(zone, delta)

    async def inc_gain(self, zone: str, delta: float) -> float:
        """Increment gain by delta dB. Returns new absolute value."""
        async with self._lock:
            resp = await self._send_recv(f"INC {self._zone_tag(zone)}.GAIN {delta:.2f}")
        return self._parse_float_response(resp)

    # ── Zone mute ──────────────────────────────────────────────────────────────

    async def get_mute(self, zone: str) -> bool:
        """Return mute state. GET ZONE-X.MUTE → +ZONE-X.MUTE 0/1."""
        async with self._lock:
            resp = await self._send_recv(f"GET {self._zone_tag(zone)}.MUTE")
        return self._parse_bool_response(resp)

    async def set_mute(self, zone: str, muted: bool) -> None:
        """Set mute state. Device expects 1/0 numeric values."""
        value = "1" if muted else "0"
        async with self._lock:
            await self._send_fire(f"SET {self._zone_tag(zone)}.MUTE {value}")

    async def set_all_mute(self, muted: bool, zones: list[str]) -> None:
        """Mute or unmute all given zones sequentially."""
        for zone in zones:
            await self.set_mute(zone, muted)

    async def close(self) -> None:
        if self._ws and not self._ws.closed:
            await self._ws.close()
