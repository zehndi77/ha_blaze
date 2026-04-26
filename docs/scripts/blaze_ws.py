"""WebSocket example for Blaze Pascal series amplifiers.

Adapted from Blaze Open API for Installers v8, section 4.3.3.
Requires: pip install websockets

Usage:
    python blaze_ws.py 192.168.64.100
    python blaze_ws.py 192.168.64.100 "GET ZONE-A.GAIN"
"""
import sys

try:
    from websockets.sync.client import connect
except ImportError:
    print("Install websockets: pip install websockets")
    sys.exit(1)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "192.168.64.100"
CUSTOM_CMD = sys.argv[2] if len(sys.argv) > 2 else None


def send(ws, cmd: str, timeout: float = 2.0) -> list[str]:
    """Send command, collect all response lines until * echo."""
    print(f">> {cmd}")
    ws.send(cmd)
    lines: list[str] = []
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            msg = ws.recv(timeout=max(0.1, deadline - time.time()))
        except TimeoutError:
            break
        for line in msg.splitlines():
            line = line.strip()
            if not line:
                continue
            lines.append(line)
            print(f"<< {line}")
            if line.startswith(f"*{cmd}"):
                return lines
    return lines


def get_device_info(ws) -> None:
    send(ws, "GET SYSTEM.DEVICE.MODEL_NAME")
    send(ws, "GET SYSTEM.DEVICE.SERIAL")
    send(ws, "GET SYSTEM.DEVICE.FIRMWARE")
    send(ws, "GET ZONE.COUNT")
    send(ws, "GET SYSTEM.STATUS.STATE")


def get_all_zones(ws) -> None:
    for zone in ("A", "B", "C", "D"):
        send(ws, f"GET ZONE-{zone}.GAIN")
        send(ws, f"GET ZONE-{zone}.MUTE")


def subscribe_all(ws, count: int = 5) -> None:
    print(">> SUBSCRIBE *")
    ws.send("SUBSCRIBE *")
    for _ in range(count):
        try:
            msg = ws.recv(timeout=1.0)
            print(msg)
        except TimeoutError:
            break


if __name__ == "__main__":
    url = f"ws://{TARGET}/ws"
    print(f"Connecting to {url}")
    with connect(url) as ws:
        if CUSTOM_CMD:
            send(ws, CUSTOM_CMD)
        else:
            get_device_info(ws)
            get_all_zones(ws)
