# Changelog

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
