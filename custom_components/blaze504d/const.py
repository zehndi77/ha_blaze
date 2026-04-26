DOMAIN = "blaze504d"
PLATFORMS = ["number", "switch", "sensor"]

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
