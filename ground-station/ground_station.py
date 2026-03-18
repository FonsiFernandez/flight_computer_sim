import subprocess
import sys
import re
import threading
import queue
from collections import deque

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

EXECUTABLE_PATH = r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software\cmake-build-debug\flight_computer_sim.exe"

TELEMETRY_PATTERN = re.compile(
    r"TIME=(?P<time>\d+)\s+ms\s+\|\s+MODE=(?P<mode>[A-Z_]+)\s+\|\s+"
    r"IMU\[x=(?P<ax>-?\d+\.\d+)\s+y=(?P<ay>-?\d+\.\d+)\s+z=(?P<az>-?\d+\.\d+)\s+valid=(?P<imu_valid>[01])\]\s+\|\s+"
    r"ALT\[(?P<alt>-?\d+\.\d+)\s+m\s+valid=(?P<alt_valid>[01])\]"
)

MAX_POINTS = 200


class GroundStation:
    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.process = None
        self.anim = None

        self.output_queue = queue.Queue()

        self.times = deque(maxlen=MAX_POINTS)
        self.altitudes = deque(maxlen=MAX_POINTS)

        self.latest_mode = "UNKNOWN"
        self.reader_thread = None
        self.running = False

    def start_simulator(self):
        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            print(f"Executable not found: {self.executable_path}")
            sys.exit(1)

    def start_reader_thread(self):
        self.running = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self):
        if self.process is None or self.process.stdout is None:
            return

        while self.running:
            line = self.process.stdout.readline()
            if not line:
                break

            self.output_queue.put(line.strip())

    def parse_telemetry(self, line: str):
        match = TELEMETRY_PATTERN.search(line)
        if not match:
            return None

        return {
            "time_ms": int(match.group("time")),
            "mode": match.group("mode"),
            "ax": float(match.group("ax")),
            "ay": float(match.group("ay")),
            "az": float(match.group("az")),
            "imu_valid": int(match.group("imu_valid")),
            "alt": float(match.group("alt")),
            "alt_valid": int(match.group("alt_valid")),
        }

    def consume_available_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get()

            print(f"[SIM] {line}")

            telemetry = self.parse_telemetry(line)
            if telemetry is None:
                continue

            time_s = telemetry["time_ms"] / 1000.0
            altitude = telemetry["alt"]
            mode = telemetry["mode"]

            self.times.append(time_s)
            self.altitudes.append(altitude)
            self.latest_mode = mode

    def update_plot(self, _frame):
        self.consume_available_output()

        plt.cla()

        if len(self.times) > 0:
            plt.plot(self.times, self.altitudes, label="Altitude [m]")

        plt.title(f"Ground Station | Mode: {self.latest_mode}")
        plt.xlabel("Time [s]")
        plt.ylabel("Altitude [m]")
        plt.grid(True)
        plt.legend()

    def run(self):
        self.start_simulator()
        self.start_reader_thread()

        plt.figure(figsize=(10, 6))
        self.anim = FuncAnimation(
            plt.gcf(),
            self.update_plot,
            interval=500,
            cache_frame_data=False
        )

        try:
            plt.tight_layout()
            plt.show()
        finally:
            self.running = False

            if self.process and self.process.poll() is None:
                self.process.terminate()


if __name__ == "__main__":
    gs = GroundStation(EXECUTABLE_PATH)
    gs.run()