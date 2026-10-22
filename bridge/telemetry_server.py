"""
Real-time Telemetry Bridge Server (Python -> Godot 3D).
Streams warehouse fleet state via high-performance TCP / WebSocket connection.
Accepts playback and camera control commands from Godot HUD.
"""

import sys
from pathlib import Path
import socket
import threading
import json
import time
from typing import Optional, Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from warehouse import ROWS, COLS
from core.sim_engine import WarehouseSimEngine
from baselines.nearest_robot import NearestRobotPolicy
from rl.environment import WarehouseFleetEnv


def grid_to_godot_world(row: int, col: int) -> Tuple[float, float]:
    """
    Transforms grid coordinate (row, col) into Godot 3D world (x, z).
    Floor width: 120.0 (X), Floor depth: 100.0 (Z).
    """
    x = (col / float(COLS - 1)) * 100.0 - 50.0
    z = (row / float(ROWS - 1)) * 80.0 - 40.0
    return (round(x, 3), round(z, 3))


class TelemetryServer:
    """
    High-throughput non-blocking TCP socket server for Godot 3D client.
    Streams newline-delimited JSON state snapshots at 30-60 Hz.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        engine: Optional[WarehouseSimEngine] = None
    ):
        self.host = host
        self.port = port
        self.engine = engine or WarehouseSimEngine(num_robots=5, enable_battery=True)
        self.policy = NearestRobotPolicy()
        self.running = False
        self.paused = False
        self.time_scale = 1.0
        self.clients = []
        self._lock = threading.Lock()

    def start(self, run_sim_loop: bool = True):
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(5)
        self.server_sock.settimeout(1.0)

        print(f"\n[TELEMETRY SERVER] Listening for Godot 3D connection on {self.host}:{self.port}")

        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()

        if run_sim_loop:
            self.sim_thread = threading.Thread(target=self._sim_loop, daemon=True)
            self.sim_thread.start()

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_sock.accept()
                client_sock.setblocking(False)
                print(f"[TELEMETRY SERVER] Godot 3D client connected from {addr}")
                with self._lock:
                    self.clients.append(client_sock)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[TELEMETRY SERVER] Accept error: {e}")
                break

    def _read_client_commands(self):
        with self._lock:
            disconnected = []
            for client in self.clients:
                try:
                    data = client.recv(1024)
                    if data:
                        lines = data.decode("utf-8").strip().split("\n")
                        for line in lines:
                            if not line:
                                continue
                            try:
                                cmd_obj = json.loads(line)
                                self._handle_command(cmd_obj)
                            except Exception:
                                pass
                except BlockingIOError:
                    pass
                except Exception:
                    disconnected.append(client)

            for d in disconnected:
                self.clients.remove(d)

    def _handle_command(self, cmd: Dict[str, Any]):
        action = cmd.get("cmd")
        if action == "pause":
            self.paused = True
            print("[TELEMETRY SERVER] Simulation Paused by Godot client")
        elif action == "play":
            self.paused = False
            print("[TELEMETRY SERVER] Simulation Resumed by Godot client")
        elif action == "reset":
            self.engine.reset()
            print("[TELEMETRY SERVER] Simulation Reset by Godot client")
        elif action == "speed":
            self.time_scale = float(cmd.get("value", 1.0))
            print(f"[TELEMETRY SERVER] Speed set to: {self.time_scale}x")

    def broadcast_state(self, state_dict: Dict[str, Any]):
        payload = json.dumps(state_dict) + "\n"
        encoded = payload.encode("utf-8")

        with self._lock:
            disconnected = []
            for client in self.clients:
                try:
                    client.sendall(encoded)
                except Exception:
                    disconnected.append(client)

            for d in disconnected:
                self.clients.remove(d)

    def _sim_loop(self):
        """Generates continuous simulation steps and streams them to Godot."""
        last_step_time = time.time()
        base_step_interval = 0.08  # ~12.5 ticks per second (smooth motion)

        while self.running:
            self._read_client_commands()

            if not self.paused:
                # Dispatch tasks for idle robots
                for r in self.engine.robots:
                    if r.current_task is None and not r.is_faulty and self.engine.waiting_tasks:
                        task = self.engine.waiting_tasks[0]
                        self.engine.assign_task_to_robot(r.robot_id, task.task_id)

                # Dynamic task arrivals
                if self.engine.current_step % 35 == 0 or len(self.engine.waiting_tasks) < 2:
                    self.engine.add_new_scenario_task()

                step_data = self.engine.step()

                # Add Godot world coordinates
                for r_info in step_data["robots"]:
                    world_x, world_z = grid_to_godot_world(r_info["row"], r_info["col"])
                    r_info["world_x"] = world_x
                    r_info["world_y"] = 0.25
                    r_info["world_z"] = world_z

                self.broadcast_state(step_data)

            sleep_dur = max(0.01, base_step_interval / max(0.1, self.time_scale))
            time.sleep(sleep_dur)

    def stop(self):
        self.running = False
        with self._lock:
            for client in self.clients:
                try:
                    client.close()
                except Exception:
                    pass
            self.clients.clear()
        if hasattr(self, "server_sock"):
            try:
                self.server_sock.close()
            except Exception:
                pass


if __name__ == "__main__":
    server = TelemetryServer()
    server.start(run_sim_loop=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
