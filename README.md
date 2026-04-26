# Blaze PowerZone Connect — Home Assistant Integration

Control your **Blaze PowerZone Connect** amplifier from Home Assistant. Set zone gain levels, mute individual zones, monitor input and output signal levels — no YAML required. Supports 2-channel, 4-channel, and 8-channel variants with automatic device detection.

---

## Features

| Entity | Type | Default | Description |
|--------|------|---------|-------------|
| Zone A–N Gain | `number` (slider, dB) | Enabled | Read and set gain per zone |
| Zone A–N Mute | `switch` | Enabled | Mute or unmute individual zones |
| All Zones Mute | `switch` | Enabled | Mute/unmute all zones simultaneously |
| Power | `switch` | Enabled | Power on / standby |
| System State | `sensor` | Enabled | INIT / STANDBY / ON / FAULT |
| Input 1–N Signal | `sensor` (dB) | **Disabled** | Analog input signal level |
| SPDIF L/R Signal | `sensor` (dB) | **Disabled** | SPDIF input signal level |
| Dante 1–4 Signal | `sensor` (dB) | **Disabled** | Dante input signal level |
| Output 1–N Signal | `sensor` (dB) | **Disabled** | Output signal level |

The integration talks to your amp over WebSocket (`ws://<host>/ws`) using the native text command protocol — no custom firmware or middleware needed.

Zone count, input count, and output count are all detected automatically on first connection.

---

## Requirements

- Home Assistant 2024.1 or newer
- Blaze PowerZone Connect reachable on your network
- (Optional) [HACS](https://hacs.xyz) for easy installation and updates

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/zehndi77/ha_blaze` as an **Integration**
3. Search for **Blaze PowerZone Connect** and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/blaze504d/` into your HA `config/custom_components/` folder
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Blaze**
3. Enter the **IP address or hostname** of your amplifier
4. Give it a friendly name (optional)
5. Click Submit — HA will verify connectivity and auto-detect zone/input/output counts before saving

Repeat for each amplifier. Each amp becomes its own HA device.

---

## Entities

### Zone Gain

- **Unit:** dB, **Range:** –80.0 to 0.0 dB (step 0.5)
- Appears as a slider in the HA dashboard
- Zone count auto-detected: 2, 4, or 8 zones depending on device variant

### Zone Mute

- Per-zone mute switch; reflects live state (polled every 30 s)
- Uses numeric `1`/`0` values per API spec

### All Zones Mute

- **ON** only when every zone is muted
- Continues through all zones even when individual zones don't respond (merged zone support)

### Signal Level Sensors (disabled by default)

Input and output signal sensors show live dB levels from `DYN.SIGNAL` registers. They are **disabled by default** to avoid unnecessary polling overhead.

To enable: go to **Settings → Devices & Services → [your amp] → Entities**, find the sensor, click it, and toggle Enable.

Once at least one signal sensor is enabled, a separate 60 s poll cycle starts for all signal readings. Analog inputs, SPDIF L/R, and Dante 1–4 are all available.

---

## Protocol Notes

The Blaze PowerZone exposes a WebSocket endpoint at `ws://<host>/ws`. Commands are plain text:

```
GET ZONE-A.GAIN          → +ZONE-A.GAIN -10.00        (read gain)
INC ZONE-A.GAIN -3       → +ZONE-A.GAIN -13.00        (adjust gain)
GET ZONE-A.MUTE          → +ZONE-A.MUTE 0              (0 = unmuted, 1 = muted)
SET ZONE-A.MUTE 1        → *SET ZONE-A.MUTE 1          (echo only)
GET IN.COUNT             → +IN.COUNT 4
GET OUTPUT.COUNT         → +OUTPUT.COUNT 4
GET IN-100.DYN.SIGNAL    → +IN-100.DYN.SIGNAL -12.50
GET OUT-1.DYN.SIGNAL     → +OUT-1.DYN.SIGNAL -8.00
```

Response lines starting with `+` carry values; lines starting with `*` are command echoes.

---

## Development & Testing

```bash
# Clone and install test dependencies
git clone https://github.com/zehndi77/ha_blaze
cd blaze504d-ha
pip install -r requirements_test.txt

# Run tests
pytest tests/ -v

# Live device test (replace IP)
python3 - <<'EOF'
import asyncio, aiohttp
from custom_components.blaze504d.blaze_client import BlazeClient

async def main():
    async with aiohttp.ClientSession() as session:
        client = BlazeClient(session, "10.17.10.31")
        print("Zone A gain:", await client.get_gain("A"))
        print("Zone A muted:", await client.get_mute("A"))
        print("Input count:", await client.get_input_count())
        print("Output count:", await client.get_output_count())

asyncio.run(main())
EOF
```

---

## Future Roadmap

- Zone source selection (input routing)
- Push-mode updates via `SUBSCRIBE` command

---

## License

MIT
