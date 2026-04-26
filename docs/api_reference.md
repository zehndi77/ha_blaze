# Blaze Pascal Series Amplifier — Open API Reference

This document describes the Open API for Blaze Pascal series amplifiers. The API is line-based and transport-agnostic: the same register/command syntax works over a raw TCP socket or WebSocket connection. It is intended for integrators building control systems, automation bridges, or custom user interfaces.

---

## Transport

### TCP Raw Socket
- **Port:** 7621
- **Framing:** line-based (`\n`-delimited)

### WebSocket
- **URL:** `ws://{host}/ws`
- **Syntax:** identical to TCP; each WebSocket message may contain multiple lines

### mDNS Discovery
- **Service type:** `_pasconnect._tcp`
- **Properties:**
  - `api_version`
  - `device_type` — always `PasAmpControl`
  - `model`
  - `software_id`
  - `hardware_id`

---

## Response Format

| Prefix | Meaning |
|--------|---------|
| `+{REGISTER} {VALUE}` | Data response — arrives before the echo |
| `*{COMMAND}` | Echo / success confirmation |
| `#{Error Message}` | Failure |

---

## Commands

### GET
```
GET {REGISTER}
```
Wildcard `*` is supported (e.g., `GET *`, `GET IN-*.NAME`).

### SET
```
SET {REGISTER} {VALUE}
```
No wildcards.

### INC
```
INC {REGISTER} {VALUE}
```
Numeric increment. No wildcards.

### SUBSCRIBE
```
SUBSCRIBE [BLANK|*|REG|DYN] [FREQ]
```
Stream register updates. `FREQ`: `1` = 1 Hz, `0.5` = 0.2 Hz.

### UNSUBSCRIBE
```
UNSUBSCRIBE [BLANK|*|REG|DYN]
```

### POWER_ON
```
POWER_ON
```
Response: `*POWER_ON`

### POWER_OFF
```
POWER_OFF
```
Response: `*POWER_OFF`

---

## Device Variants

| Variant | Zones | Outputs | Analog Inputs |
|---------|-------|---------|---------------|
| 2-channel | A, B | 1–2 | 100–101 |
| 4-channel | A–D | 1–4 | 100–103 |
| 8-channel | A–H | 1–8 | 100–107 |

---

## ID Reference

### Input Source IDs (`{SID}`)

| ID | Source |
|----|--------|
| 0 | Silent |
| 100–107 | Analog Input 1–8 |
| 200–201 | SPDIF L/R |
| 300–303 | Dante 1–4 |
| 400 | Noise Generator |
| 500–507 | Mix 1–8 |

### Zone IDs (`{ZID}`)

| Variant | Zone IDs |
|---------|----------|
| 2-channel | A, B |
| 4-channel | A, B, C, D |
| 8-channel | A, B, C, D, E, F, G, H |

### Output IDs (`{OID}`)

| Variant | Output IDs |
|---------|-----------|
| All | 1, 2 |
| 4-channel / 8-channel | + 3, 4 |
| 8-channel only | + 5, 6, 7, 8 |

---

## Register Reference

### Base Status Registers

| Register | Type | Access | Notes |
|----------|------|--------|-------|
| `API_VERSION` | String | Get | API version string |
| `SYSTEM.STATUS.STATE` | Enum | Get | `INIT`, `STANDBY`, `ON`, `FAULT` |
| `SYSTEM.STATUS.SIGNAL_IN` | Enum | Get | `OFF`, `NO_SIGNAL`, `SIGNAL`, `CLIP` |
| `SYSTEM.STATUS.SIGNAL_OUT` | Enum | Get | `OFF`, `NO_SIGNAL`, `SIGNAL`, `CLIP`, `FAULT` |
| `SYSTEM.STATUS.LAN` | String | Get | IP address or empty |
| `SYSTEM.STATUS.WIFI` | String | Get | IP address or empty |

### Device Information Registers (read-only)

| Register | Type | Access | Notes |
|----------|------|--------|-------|
| `SYSTEM.DEVICE.SWID` | Integer | Get | Software ID |
| `SYSTEM.DEVICE.HWID` | Integer | Get | Hardware ID (model variant) |
| `SYSTEM.DEVICE.VENDOR_NAME` | String | Get | Max 32 chars |
| `SYSTEM.DEVICE.MODEL_NAME` | String | Get | Max 32 chars |
| `SYSTEM.DEVICE.SERIAL` | String | Get | Max 32 chars, e.g. `2122023201X00031` |
| `SYSTEM.DEVICE.FIRMWARE` | String | Get | e.g. `1.6.0` |
| `SYSTEM.DEVICE.FIRMWARE_DATE` | String | Get | e.g. `Nov 5 2021 07:51:56` |
| `SYSTEM.DEVICE.MAC` | String | Get | Ethernet MAC |
| `SYSTEM.DEVICE.WIFI_MAC` | String | Get | WiFi MAC |

### System Info Registers (read/write)

| Register | Type | Access | Notes |
|----------|------|--------|-------|
| `SETUP.SYSTEM.DEVICE_NAME` | String[32] | Get, Set | User-assigned device name |
| `SETUP.SYSTEM.VENUE_NAME` | String[32] | Get, Set | |
| `SETUP.SYSTEM.CUSTOMER_NAME` | String[32] | Get, Set | |
| `SETUP.SYSTEM.ASSET_TAG` | String[32] | Get, Set | |
| `SETUP.SYSTEM.INSTALLER_NAME` | String[32] | Get, Set | |
| `SETUP.SYSTEM.CONTACT_INFO` | String[32] | Get, Set | |
| `SETUP.SYSTEM.INSTALL_DATE` | String[32] | Get, Set | |
| `SETUP.SYSTEM.INSTALL_NOTES` | String[512] | Get, Set | |
| `SETUP.SYSTEM.LOCATING` | Boolean | Get, Set | |
| `SETUP.SYSTEM.CUSTOM1` | String[8192] | Get, Set | |
| `SETUP.SYSTEM.CUSTOM2` | String[8192] | Get, Set | |
| `SETUP.SYSTEM.CUSTOM3` | String[8192] | Get, Set | |

### Zone Registers — `{ZID}` = A–D (4ch) or A–H (8ch)

| Register | Type | Access | Range | Notes |
|----------|------|--------|-------|-------|
| `ZONE.COUNT` | Integer | Get | 2, 4, 8 | Total zone count |
| `ZONE-{ZID}.NAME` | String | Get, Set | | |
| `ZONE-{ZID}.PRIMARY_SRC` | Integer | Get, Set | See `{SID}` | Primary input source |
| `ZONE-{ZID}.PRIORITY_SRC` | Integer | Get, Set | See `{SID}` | Priority input source |
| `ZONE-{ZID}.GAIN` | Float | Get, Set, INC | dB | Use GET for reading |
| `ZONE-{ZID}.GAIN_MIN` | Float | Get | dB | Default -80.0 |
| `ZONE-{ZID}.GAIN_MAX` | Float | Get | dB | Default 0.0 |
| `ZONE-{ZID}.STEREO` | Boolean | Get, Set | | |
| `ZONE-{ZID}.GPIO_VC` | Integer | Get, Set | | GPIO volume control |
| `ZONE-{ZID}.MUTE` | Boolean | Get, Set | `0`/`1` or `ON`/`OFF` | Mute state |
| `ZONE-{ZID}.MUTE_ENABLE` | Boolean | Get, Set | | Enable mute control |
| `ZONE-{ZID}.SRC-{SID}.ENABLED` | Boolean | Get, Set | | Enable source for zone |
| `ZONE-{ZID}.DYN.SIGNAL` | Float | Get | dB | Dynamic signal level |

### Input Registers — `{IID}` = 100–103 (4ch), 100–107 (8ch), 200–201 (SPDIF), 300–303 (Dante), 400 (Noise)

| Register | Type | Access | Range | Notes |
|----------|------|--------|-------|-------|
| `IN.COUNT` | Integer | Get | | Total input count |
| `IN-{IID}.NAME` | String | Get, Set | | Input name |
| `IN-{IID}.SENS` | Float | Get, Set | dB | Sensitivity |
| `IN-{IID}.GAIN` | Float | Get, Set, INC | dB | [-15, 15] |
| `IN-{IID}.STEREO` | Boolean | Get, Set | | |
| `IN-{IID}.HPF_ENABLE` | Boolean | Get, Set | | High-pass filter |
| `IN-{IID}.DYN.SIGNAL` | Float | Get | dB | Dynamic signal level |
| `IN-{IID}.DYN.CLIP` | Integer | Get | | Clip indicator |

### Output Registers — `{OID}` = 1–2 (all), 3–4 (4ch+), 5–8 (8ch only)

| Register | Type | Access | Range | Notes |
|----------|------|--------|-------|-------|
| `OUTPUT.COUNT` | Integer | Get | | |
| `OUT-{OID}.NAME` | String | Get, Set | | |
| `OUT-{OID}.SRC` | Integer | Get, Set | See `{SID}` | Source routing |
| `OUT-{OID}.SRC_CHANNEL` | String | Get, Set | `S`, `L`, `R` | |
| `OUT-{OID}.POLARITY` | Boolean | Get, Set | | |
| `OUT-{OID}.OUTPUT_MODE` | Enum | Get, Set | | |
| `OUT-{OID}.OUTPUT_HIGHPASS` | Boolean | Get, Set | | |
| `OUT-{OID}.GAIN` | Float | Get, Set | dB | [-30, 15] |
| `OUT-{OID}.MUTE` | Boolean | Get, Set | | |
| `OUT-{OID}.DYN.SIGNAL` | Float | Get | dB | |
| `OUT-{OID}.DYN.CLIP` | Integer | Get | | |

### Power Management

| Register | Type | Access | Range |
|----------|------|--------|-------|
| `SETUP.POWER.POWER_ON` | Enum | Get, Set | `AUDIO`, `AUDIO_ECO`, `TRIGGER`, `TRIGGER_ECO`, `NETWORK`, `AUDIO_DSP` |
| `SETUP.POWER.MUTE_TIME` | Integer | Get, Set | Sec [0, 3600] |
| `SETUP.POWER.STANDBY_TIME` | Integer | Get, Set | Sec [0, 3600] |

### LAN / WiFi (read-only since firmware 1.3)

| Register | Type | Notes |
|----------|------|-------|
| `SETUP.LAN.NETWORK_MODE` | Enum | `STATIC`, `DHCP` |
| `SETUP.LAN.IP` | String | |
| `SETUP.LAN.MASK` | String | |
| `SETUP.LAN.GATEWAY` | String | |
| `SETUP.WIFI.ENABLE` | Boolean | |
| `SETUP.WIFI.MODE` | Enum | `AP`, `STA` |

### Advanced (requires manufacturer support)

The following register groups are available with manufacturer support:

- **Mix:** `MIX.COUNT`, `MIX-{MID}.NAME`, `MIX-{MID}.GAIN-{SID}`
- **Output Speaker Preset, Speaker Delay, Peak/RMS/Clip Limiters**
- **Output EQ, SpeakerEQ, Crossover, FIR**
- **Output Routing:** `ROUT-{RID}.SRC`, `ROUT-{RID}.GAIN`
- **Analog Volume Control:** `VC.COUNT`, `VC-{VID}.VALUE` (percent, read-only)
- **GPIO:** `SETUP.GPIO.PIN2`, `SETUP.GPIO.PIN4`, `SETUP.GPIO.PIN5`, `SETUP.GPIO.PIN6`, `SETUP.GPIO.PIN7`, `SETUP.GPIO.PIN8`
- **Security:** `SYSTEM.SECURITY.PASSWORD_ENABLE`, `SYSTEM.SECURITY.PASSWORD_HASH`
- **Dante:** `SYSTEM.DANTE.*`
