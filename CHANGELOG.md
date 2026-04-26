# Changelog

## [0.3.0] - 2026-04-26

### Changed
- **Signal sensors now use push subscription** instead of individual GET polls. On setup the integration sends `SUBSCRIBE DYN 1` and the device pushes all `DYN.SIGNAL` values at 1 Hz. The `BlazeSignalCoordinator` reads from a local cache populated by these pushes — no per-sensor GET commands issued during polling
- **Entity naming** (`_attr_has_entity_name = True`): all entities are now scoped to their device in the HA entity registry. Entity IDs change from `sensor.dante_2_signal` to `sensor.{device_name}_dante_2_signal`. **Action required**: delete any signal sensor entities showing "no unique ID" from HA's entity registry (Settings → Devices & Services → device → Entities), then reload the integration

### Fixed
- **Signal sensors returning no data**: previous GET-based DYN polling timed out because the device delivers DYN values via subscription push, not GET responses
- **Reader-loop multiplexer**: a background `_reader_task` now owns all incoming WebSocket reads. Subscription DYN pushes go to an internal cache; command responses route to the waiting `asyncio.Future`. Eliminates the race where a DYN push could resolve the wrong command future
- Lock ownership moved inside `_send_recv`/`_send_fire` (was in callers). Prevents a latent double-lock deadlock when callers chain two commands. Behaviour unchanged — one command in-flight at a time
- `close()` now awaits the cancelled reader task, preventing resource leaks on integration unload

## [0.2.2] - 2026-04-26

### Added
- **Input signal sensors** (`sensor`): per-input signal level in dB — analog inputs (Input 1–N), SPDIF L/R, and Dante 1–4. All disabled by default; enable individually in the HA entity registry
- **Output signal sensors** (`sensor`): per-output signal level in dB (Output 1–N). Also disabled by default
- Dedicated `BlazeSignalCoordinator` polls signal levels at 60 s (separate from 30 s zone poll); starts lazily only when at least one signal sensor is enabled
- Input and output counts queried from device at startup (`GET IN.COUNT`, `GET OUTPUT.COUNT`) — independent of zone count; fallback to zone count if unavailable

### Fixed
- **WebSocket "closing transport" race**: `_send_with_retry` helper reconnects once on `ClientConnectionResetError` before raising — eliminates the dominant cause of coordinator poll failures and 30 s entity unavailability
- **Mute command timeouts no longer surface as HA errors**: `_send_fire` treats missing `*` echo as a warning (command was sent over reliable WebSocket; state confirmed on next poll). Fixes "Failed to perform the action" errors for merged zones
- **All-zones mute now completes all zones**: previously aborted at first timeout; now continues through all zones even when one doesn't echo
- **Coordinator per-zone resilience**: `get_gain` failures fall back to cached value (same pattern as `get_mute`), preventing a single zone query failure from marking all entities unavailable
- **Mute command format**: `SET ZONE-X.MUTE` now sends `1`/`0` instead of `ON`/`OFF` per API spec

## [0.2.0] - 2026-04-26

### Added
- **Device auto-detection**: on first connection queries `ZONE.COUNT`, `MODEL_NAME`, `SERIAL`, `FIRMWARE` — zone list configured automatically
- **Multi-variant support**: 2-channel (A,B), 4-channel (A-D), 8-channel (A-H) devices work without config changes
- **Power switch entity**: reads `SYSTEM.STATUS.STATE`, sends `POWER_ON`/`POWER_OFF` commands
- **System State sensor**: exposes `SYSTEM.STATUS.STATE` (INIT/STANDBY/ON/FAULT) as HA sensor
- **Device registry**: firmware version and serial number now shown in HA device info
- **Bruno API collection**: `bruno/blaze-api/` with documented commands for all operations
- **Test scripts**: `docs/scripts/blaze_tcp.py` and `blaze_ws.py` for live debugging
- **API reference**: `docs/api_reference.md` — complete register reference from official PDF
- TCP port constant (`TCP_PORT = 7621`) added to const.py

### Fixed
- **Critical: Zone B/C/D polling timeout** — `get_gain` switched from `INC ZONE-X.GAIN 0` to `GET ZONE-X.GAIN` (INC with 0 delta returned no `+` response; GET always returns `+VALUE` per API spec)
- `WS_TIMEOUT` raised from 5s to 10s for slower devices
- `GAIN_MIN` corrected from -60.0 to -80.0 dB per API spec
- `BlazeAllMute` now uses dynamic zone list from coordinator (not hardcoded A-D)
- `set_all_mute` accepts explicit zone list to avoid hardcoded zone assumption

### Changed
- `ZONES` constant removed from const.py; replaced by `ZONE_LETTERS_BY_COUNT` and `ALL_VALID_ZONES`
- `BlazeCoordinator` now accepts `zones: list[str]` parameter
- Zone entities created from `coordinator.zones` (dynamic), not hardcoded list
- `PLATFORMS` expanded to include `sensor`
- Existing 4-zone config entries continue to work (fallback to 4-zone if `zone_count` missing)

## [0.1.1] - 2026-04-26

### Fixed
- Polling stability: `get_gain` now uses `INC ZONE-X.GAIN 0` (no-op read) instead of unconfirmed `GET` command
- Volume set no longer times out: `set_gain` uses get-then-INC-delta, avoiding `SET` which returns no `+` response
- Multi-line WebSocket frames now parsed correctly (echo + value in single frame)
- Mute query confirmed: `GET ZONE-X.MUTE` → `+ZONE-X.MUTE 0/1`
- Mute write uses fire-and-forget (`_send_fire`) accepting `*` echo as confirmation

## [0.1.0] - 2026-04-26

### Added
- Zone gain control (dB) for all 4 zones via `number` entities
- Per-zone mute switches (Zone A–D Mute)
- Master "All Zones Mute" switch
- WebSocket client with lazy reconnection and asyncio.Lock serialization
- Config flow (UI setup) — no YAML required
- Support for multiple amplifiers as separate config entries
- HACS-compatible integration structure
