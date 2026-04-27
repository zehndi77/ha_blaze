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
        self._dyn_cache: dict[str, float] = {}
        self._dyn_subscribed = False
        self._reader_task: asyncio.Task | None = None
        self._pending_future: asyncio.Future[str] | None = None
        self._pending_recv: bool = False  # True when _send_recv awaits +value; False for _send_fire awaiting *echo
        self._pending_prefix: str | None = None  # Expected +REGISTER prefix for _send_recv; None = accept any +

    @property
    def _url(self) -> str:
        return f"ws://{self._host}{WS_PATH}"

    # ── Connection management ──────────────────────────────────────────────────

    async def _connect(self) -> None:
        try:
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(self._url),
                timeout=WS_TIMEOUT,
            )
        except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as err:
            raise BlazeConnectionError(f"Cannot connect to {self._url}: {err}") from err
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
        self._reader_task = asyncio.create_task(self._reader_loop())

    async def _ensure_connected(self) -> None:
        """Must be called with self._lock held."""
        if self._ws is None or self._ws.closed:
            await self._connect()
            if self._dyn_subscribed:
                assert self._ws is not None
                await self._ws.send_str("SUBSCRIBE DYN 1")

    # ── Reader loop (background task) ─────────────────────────────────────────

    def _handle_incoming(self, line: str) -> None:
        if not line:
            return
        _LOGGER.debug("Blaze WS recv: %r", line)

        if line.startswith("+") and ".DYN." in line:
            # Never route DYN lines to _pending_future: a subscription push arriving
            # mid-command would resolve the wrong future with the wrong register value.
            parts = line[1:].rsplit(" ", 1)
            if len(parts) == 2:
                try:
                    self._dyn_cache[parts[0]] = float(parts[1])
                except ValueError:
                    _LOGGER.debug("Cannot parse DYN value: %r", line)
            return

        fut = self._pending_future
        if fut and not fut.done():
            if line.startswith("#"):
                fut.set_result(line)
            elif line.startswith("+"):
                # Only resolve if the response register matches the one we asked for.
                # This prevents subscription pushes for unrelated registers (e.g. +VC-1.VALUE 51
                # from a hardware volume-control knob) from being misread as the gain value.
                prefix = self._pending_prefix
                if prefix is None or line.startswith(prefix):
                    fut.set_result(line)
            elif line.startswith("*") and not self._pending_recv:
                # Never resolve a _send_recv future with a * echo: a delayed echo from a
                # prior INC/SET arriving after its own lock window would corrupt the next
                # command's future (e.g. *INC ZONE-A.GAIN 51.00 → parsed as 51 dB).
                fut.set_result(line)

    async def _reader_loop(self) -> None:
        """Background task: reads all incoming WS messages until disconnect."""
        try:
            assert self._ws is not None
            while not self._ws.closed:
                msg = await self._ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    for line in msg.data.splitlines():
                        self._handle_incoming(line.strip())
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
        except Exception as err:
            _LOGGER.debug("Blaze reader loop exiting: %s", err)
        finally:
            self._ws = None
            fut = self._pending_future
            if fut and not fut.done():
                fut.set_exception(BlazeConnectionError("WebSocket disconnected"))

    # ── Command helpers ────────────────────────────────────────────────────────

    async def _send_recv(self, command: str) -> str:
        """Send a command; wait for the + value response via the reader loop.

        Acquires self._lock — callers must NOT hold it.
        """
        async with self._lock:
            await self._ensure_connected()
            assert self._ws is not None
            loop = asyncio.get_running_loop()
            self._pending_recv = True
            cmd_parts = command.split()
            self._pending_prefix = f"+{cmd_parts[1]} " if len(cmd_parts) >= 2 else None
            self._pending_future = loop.create_future()
            try:
                await self._ws.send_str(command)
                async with asyncio.timeout(WS_TIMEOUT):
                    result = await self._pending_future
            except asyncio.TimeoutError:
                self._ws = None
                raise BlazeConnectionError(f"Timeout waiting for response to '{command}'")
            except aiohttp.ClientError as err:
                self._ws = None
                raise BlazeConnectionError(f"WebSocket error: {err}") from err
            finally:
                self._pending_future = None

        if result.startswith("#"):
            raise BlazeProtocolError(f"Device error: {result!r}")
        return result

    async def _send_fire(self, command: str) -> None:
        """Send a command expecting only a * echo; timeout is non-fatal.

        Acquires self._lock — callers must NOT hold it.
        """
        async with self._lock:
            await self._ensure_connected()
            assert self._ws is not None
            loop = asyncio.get_running_loop()
            self._pending_recv = False
            self._pending_prefix = None
            self._pending_future = loop.create_future()
            try:
                await self._ws.send_str(command)
                async with asyncio.timeout(WS_TIMEOUT):
                    await self._pending_future
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "No ack for '%s' within %ss; command likely applied", command, WS_TIMEOUT
                )
                self._ws = None
            except aiohttp.ClientError as err:
                self._ws = None
                raise BlazeConnectionError(f"WebSocket error: {err}") from err
            finally:
                self._pending_future = None

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

    # ── DYN subscription ───────────────────────────────────────────────────────

    async def start_dyn_subscription(self, freq: float = 1.0) -> None:
        """Subscribe to DYN register push updates at the given frequency (Hz)."""
        async with self._lock:
            await self._ensure_connected()
            assert self._ws is not None
            self._dyn_subscribed = True
            await self._ws.send_str(f"SUBSCRIBE DYN {freq}")

    def get_dyn_snapshot(self) -> dict[str, float]:
        """Return a snapshot of the current DYN register cache."""
        return dict(self._dyn_cache)

    # ── Device info ────────────────────────────────────────────────────────────

    async def get_zone_count(self) -> int:
        resp = await self._send_recv("GET ZONE.COUNT")
        return int(self._parse_float_response(resp))

    async def get_model_name(self) -> str:
        resp = await self._send_recv("GET SYSTEM.DEVICE.MODEL_NAME")
        return self._parse_str_response(resp)

    async def get_serial(self) -> str:
        resp = await self._send_recv("GET SYSTEM.DEVICE.SERIAL")
        return self._parse_str_response(resp)

    async def get_firmware(self) -> str:
        resp = await self._send_recv("GET SYSTEM.DEVICE.FIRMWARE")
        return self._parse_str_response(resp)

    async def get_device_info(self) -> dict:
        """Return zone_count, model_name, serial, firmware."""
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
        resp = await self._send_recv("GET SYSTEM.STATUS.STATE")
        return self._parse_str_response(resp)

    # ── I/O counts ────────────────────────────────────────────────────────────

    async def get_input_count(self) -> int:
        resp = await self._send_recv("GET IN.COUNT")
        return int(self._parse_float_response(resp))

    async def get_output_count(self) -> int:
        resp = await self._send_recv("GET OUTPUT.COUNT")
        return int(self._parse_float_response(resp))

    # ── Power ──────────────────────────────────────────────────────────────────

    async def power_on(self) -> None:
        await self._send_fire("POWER_ON")

    async def power_off(self) -> None:
        await self._send_fire("POWER_OFF")

    # ── Zone gain ──────────────────────────────────────────────────────────────

    async def get_gain(self, zone: str) -> float:
        """Return current gain in dB."""
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
        resp = await self._send_recv(f"INC {self._zone_tag(zone)}.GAIN {delta:.2f}")
        return self._parse_float_response(resp)

    # ── Zone mute ──────────────────────────────────────────────────────────────

    async def get_mute(self, zone: str) -> bool:
        """Return mute state. GET ZONE-X.MUTE → +ZONE-X.MUTE 0/1."""
        resp = await self._send_recv(f"GET {self._zone_tag(zone)}.MUTE")
        return self._parse_bool_response(resp)

    async def set_mute(self, zone: str, muted: bool) -> None:
        """Set mute state. Device expects 1/0 numeric values."""
        value = "1" if muted else "0"
        await self._send_fire(f"SET {self._zone_tag(zone)}.MUTE {value}")

    async def set_all_mute(self, muted: bool, zones: list[str]) -> None:
        """Mute or unmute all given zones sequentially."""
        for zone in zones:
            await self.set_mute(zone, muted)

    async def close(self) -> None:
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._ws and not self._ws.closed:
            await self._ws.close()
