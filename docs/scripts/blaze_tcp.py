"""TCP socket example for Blaze Pascal series amplifiers.

Adapted from Blaze Open API for Installers v8, section 4.3.2.
Connect on port 7621; every line is a single message, delimited by \\n.

Usage:
    python blaze_tcp.py 192.168.64.100
"""
import socket
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "192.168.64.100"
PORT = 7621


def send_command(sock: socket.socket, cmd: str) -> list[str]:
    """Send a command and collect response lines until the echo (*CMD) arrives."""
    sock.sendall((cmd + "\n").encode())
    lines: list[str] = []
    buf = b""
    while True:
        chunk = sock.recv(64 * 1024)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line_bytes, buf = buf.split(b"\n", 1)
            line = line_bytes.decode().strip()
            if not line:
                continue
            lines.append(line)
            print(f"<< {line}")
            if line.startswith(f"*{cmd}"):
                return lines
    return lines


def get_all(sock: socket.socket) -> None:
    print(">> GET *")
    sock.sendall(b"GET *\n")
    buf = b""
    while True:
        chunk = sock.recv(64 * 1024)
        if not chunk:
            break
        buf += chunk
        decoded = buf.decode(errors="replace")
        print(decoded, end="")
        if "*GET *" in decoded:
            break


def subscribe_all(sock: socket.socket, count: int = 5) -> None:
    print(">> SUBSCRIBE *")
    sock.sendall(b"SUBSCRIBE *\n")
    for _ in range(count):
        reply = sock.recv(64 * 1024)
        if reply:
            print(reply.decode(errors="replace"), end="")


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TARGET, PORT))
        print(f"Connected to {TARGET}:{PORT}")

        # Device info
        send_command(s, "GET SYSTEM.DEVICE.MODEL_NAME")
        send_command(s, "GET SYSTEM.DEVICE.SERIAL")
        send_command(s, "GET SYSTEM.DEVICE.FIRMWARE")
        send_command(s, "GET ZONE.COUNT")
        send_command(s, "GET SYSTEM.STATUS.STATE")

        # Zone A gain
        send_command(s, "GET ZONE-A.GAIN")
