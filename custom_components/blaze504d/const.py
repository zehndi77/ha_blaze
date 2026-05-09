DOMAIN = "blaze504d"
PLATFORMS = ["number", "select", "switch", "sensor"]

CONF_HOST = "host"
CONF_NAME = "name"
CONF_ZONE_COUNT = "zone_count"
CONF_MODEL_NAME = "model_name"
CONF_SERIAL = "serial"
CONF_FIRMWARE = "firmware"

ZONE_LETTERS_BY_COUNT: dict[int, list[str]] = {
    2: ["A", "B"],
    4: ["A", "B", "C", "D"],
    8: ["A", "B", "C", "D", "E", "F", "G", "H"],
}
ALL_VALID_ZONES = ["A", "B", "C", "D", "E", "F", "G", "H"]
DEFAULT_ZONE_COUNT = 4

GAIN_MIN = -80.0
GAIN_MAX = 0.0
GAIN_STEP = 0.5

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SIGNAL_SCAN_INTERVAL = 60

WS_PORT = 80
WS_PATH = "/ws"
WS_TIMEOUT = 10
TCP_PORT = 7621

CONF_INPUT_COUNT = "input_count"
CONF_OUTPUT_COUNT = "output_count"
ANALOG_INPUT_BASE_ID = 100
OUTPUT_BASE_ID = 1
SPDIF_INPUT_IDS = [200, 201]
DANTE_INPUT_IDS = [300, 301, 302, 303]

INPUT_SOURCE_MAP: dict[int, str] = {
    0: "Silent",
    100: "Analog 1",
    101: "Analog 2",
    102: "Analog 3",
    103: "Analog 4",
    104: "Analog 5",
    105: "Analog 6",
    106: "Analog 7",
    107: "Analog 8",
    200: "SPDIF 1 (Left)",
    201: "SPDIF 1 (Right)",
    300: "Dante 1",
    301: "Dante 2",
    302: "Dante 3",
    303: "Dante 4",
    400: "Noise Generator",
    500: "Mix 1",
    501: "Mix 2",
    502: "Mix 3",
    503: "Mix 4",
    504: "Mix 5",
    505: "Mix 6",
    506: "Mix 7",
    507: "Mix 8",
}
INPUT_SOURCE_ID_BY_NAME: dict[str, int] = {v: k for k, v in INPUT_SOURCE_MAP.items()}
