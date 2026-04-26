# Blaze PowerZone Connect 504D — Home Assistant Integration

Control your **Blaze PowerZone Connect 504D** amplifier from Home Assistant. Set zone gain levels, mute individual zones, and mute all zones at once — no YAML required.

---

## Features

| Entity | Type | Description |
|--------|------|-------------|
| Zone A–D Gain | `number` (slider, dB) | Read and set gain for each zone |
| Zone A–D Mute | `switch` | Mute or unmute individual zones |
| All Zones Mute | `switch` | Mute/unmute all 4 zones simultaneously |

The integration talks to your amp over WebSocket (`ws://<host>/ws`) using the native text command protocol — no custom firmware or middleware needed.

---

## Requirements

- Home Assistant 2024.1 or newer
- Blaze PowerZone Connect 504D reachable on your network
- (Optional) [HACS](https://hacs.xyz) for easy installation and updates

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/zehndi77/ha_blaze` as an **Integration**
3. Search for **Blaze PowerZone Connect 504D** and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/blaze504d/` into your HA `config/custom_components/` folder
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Blaze 504D**
3. Enter the **IP address or hostname** of your amplifier
4. Give it a friendly name (optional)
5. Click Submit — HA will verify connectivity before saving

Repeat for each amplifier. Each amp becomes its own device with 9 entities (4 gain + 4 mute + 1 master mute).

---

## Entities

### Gain (Zone A–D)

- **Entity ID:** `number.<name>_zone_a_gain` (and B/C/D)
- **Unit:** dB
- **Range:** –60.0 to 0.0 dB (step 0.5)
- Appears as a slider in the HA dashboard
- Use in automations to set absolute levels: `service: number.set_value`

### Zone Mute (Zone A–D)

- **Entity ID:** `switch.<name>_zone_a_mute` (and B/C/D)
- Mutes/unmutes one zone
- Reflects live state from the amp (polled every 30 s)

### All Zones Mute

- **Entity ID:** `switch.<name>_all_zones_mute`
- **ON** only when every zone is muted
- Turning ON mutes all 4 zones; turning OFF unmutes all 4

---

## Protocol Notes

The 504D exposes a WebSocket endpoint at `ws://<host>/ws`. Commands are plain text:

```
GET ZONE-A.GAIN          → +Zone-A.GAIN -10.00
SET ZONE-A.GAIN -15.00   → +Zone-A.GAIN -15.00
INC ZONE-A.GAIN -3       → +Zone-A.GAIN -18.00  (+ *INC ZONE-A.GAIN -3 echo)
GET ZONE-A.MUTE          → +Zone-A.MUTE OFF
SET ZONE-A.MUTE ON       → +Zone-A.MUTE ON
```

Response lines starting with `+` carry values; lines starting with `*` are command echoes and are ignored.

> **Note:** If your firmware uses a different gain range or mute command format, adjust `GAIN_MIN`, `GAIN_MAX` in `const.py` and `_parse_bool_response` in `blaze_client.py`.

---

## Development & Testing

```bash
# Clone and install test dependencies
git clone https://github.com/YOUR_GITHUB/blaze504d-ha
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

asyncio.run(main())
EOF
```

---

## Future Roadmap

- Zone source selection (input routing)
- Zone output configuration
- Push-mode updates (if the device sends unsolicited state notifications)

---

## License

MIT
