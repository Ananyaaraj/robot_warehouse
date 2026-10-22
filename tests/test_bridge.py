import pytest
import socket
import json
import time

from bridge.telemetry_server import TelemetryServer, grid_to_godot_world


def test_grid_to_godot_world_mapping():
    # Corner (0, 0)
    x0, z0 = grid_to_godot_world(0, 0)
    assert x0 == -50.0
    assert z0 == -40.0

    # Opposite corner (62, 160)
    x1, z1 = grid_to_godot_world(62, 160)
    assert x1 == 50.0
    assert z1 == 40.0


def test_telemetry_server_streaming():
    server = TelemetryServer(port=8799)
    server.start(run_sim_loop=True)

    try:
        # Connect test TCP client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3.0)
        client.connect(("127.0.0.1", 8799))

        # Receive telemetry snapshot
        data = b""
        start_time = time.time()
        while b"\n" not in data and time.time() - start_time < 3.0:
            chunk = client.recv(4096)
            data += chunk

        assert b"\n" in data, "Did not receive newline-delimited telemetry packet"
        first_line = data.decode("utf-8").strip().split("\n")[0]
        packet = json.loads(first_line)

        assert "step" in packet
        assert "robots" in packet
        assert len(packet["robots"]) == 5
        assert "world_x" in packet["robots"][0]
        assert "world_z" in packet["robots"][0]
        assert "metrics" in packet

        # Test sending command back to server
        cmd = json.dumps({"cmd": "pause"}) + "\n"
        client.sendall(cmd.encode("utf-8"))
        time.sleep(0.1)
        assert server.paused is True

        client.close()
    finally:
        server.stop()
