import subprocess
import sys
import re
import threading
import queue
import csv
from pathlib import Path
from datetime import datetime
from collections import deque
from dataclasses import dataclass


import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button


EXECUTABLE_PATH = r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software\cmake-build-debug\flight_computer_sim.exe"

TELEMETRY_PATTERN = re.compile(
    r"TIME=(?P<time>\d+)\s+ms\s+\|\s+"
    r"MODE=(?P<mode>[A-Z_]+)\s+\|\s+"
    r"IMU\[x=(?P<ax>-?\d+\.\d+)\s+y=(?P<ay>-?\d+\.\d+)\s+z=(?P<az>-?\d+\.\d+)\s+valid=(?P<imu_valid>[01])\]\s+\|\s+"
    r"ALT\[(?P<alt>-?\d+\.\d+)\s+m\s+valid=(?P<alt_valid>[01])\]\s+\|\s+"
    r"HM\[imu_fault=(?P<imu_fault>\d+)\s+imu_rec=(?P<imu_rec>\d+)\s+alt_fault=(?P<alt_fault>\d+)\s+alt_rec=(?P<alt_rec>\d+)\s+imu_lat=(?P<imu_lat>[01])\s+alt_lat=(?P<alt_lat>[01])\s+status=(?P<status>\d+)\]"
)

MAX_POINTS = 300


@dataclass
class TelemetryFrame:
    time_ms: int
    mode: str
    ax: float
    ay: float
    az: float
    imu_valid: int
    altitude_m: float
    alt_valid: int
    imu_fault_count: int
    imu_recovery_count: int
    alt_fault_count: int
    alt_recovery_count: int
    imu_latched: int
    alt_latched: int
    health_status: int


class GroundStation:
    def __init__(self, executable_path: str):
        self.executable_path = executable_path
        self.process = None
        self.anim = None
        self.output_queue = queue.Queue()

        self.reader_thread = None
        self.running = False

        self.times = deque(maxlen=MAX_POINTS)
        self.altitudes = deque(maxlen=MAX_POINTS)
        self.accel_x = deque(maxlen=MAX_POINTS)
        self.accel_y = deque(maxlen=MAX_POINTS)
        self.accel_z = deque(maxlen=MAX_POINTS)

        self.latest_frame = None
        self.latest_mode = "UNKNOWN"

        self.csv_file = None
        self.csv_writer = None
        self.csv_path = None

    def start_simulator(self):
        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
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

        return TelemetryFrame(
            time_ms=int(match.group("time")),
            mode=match.group("mode"),
            ax=float(match.group("ax")),
            ay=float(match.group("ay")),
            az=float(match.group("az")),
            imu_valid=int(match.group("imu_valid")),
            altitude_m=float(match.group("alt")),
            alt_valid=int(match.group("alt_valid")),
            imu_fault_count=int(match.group("imu_fault")),
            imu_recovery_count=int(match.group("imu_rec")),
            alt_fault_count=int(match.group("alt_fault")),
            alt_recovery_count=int(match.group("alt_rec")),
            imu_latched=int(match.group("imu_lat")),
            alt_latched=int(match.group("alt_lat")),
            health_status=int(match.group("status")),
        )

    def consume_available_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get()

            print(f"[SIM] {line}")

            telemetry = self.parse_telemetry(line)
            if telemetry is None:
                continue

            time_s = telemetry.time_ms / 1000.0

            self.times.append(time_s)
            self.altitudes.append(telemetry.altitude_m)
            self.accel_x.append(telemetry.ax)
            self.accel_y.append(telemetry.ay)
            self.accel_z.append(telemetry.az)

            self.latest_frame = telemetry
            self.latest_mode = telemetry.mode

            self.log_frame_to_csv(telemetry)

    @staticmethod
    def mode_color(mode: str):
        if mode == "NOMINAL":
            return "#d8f5d0"
        if mode == "DEGRADED":
            return "#ffe8bf"
        if mode == "SAFE":
            return "#ffd6d6"
        return "#f0f0f0"

    @staticmethod
    def health_status_text(status: int):
        if status == 0:
            return "OK"
        if status == 1:
            return "WARNING"
        if status == 2:
            return "CRITICAL"
        return "UNKNOWN"

    def update_dashboard(self, _frame):
        self.consume_available_output()

        self.ax_alt.clear()
        self.ax_az.clear()
        self.ax_xy.clear()
        self.ax_status.clear()

        bg_color = self.mode_color(self.latest_mode)

        self.ax_alt.set_facecolor(bg_color)
        self.ax_az.set_facecolor(bg_color)
        self.ax_xy.set_facecolor(bg_color)
        self.ax_status.set_facecolor(bg_color)

        if len(self.times) > 0:
            self.ax_alt.plot(self.times, self.altitudes, label="Altitude [m]")
            self.ax_az.plot(self.times, self.accel_z, label="Accel Z [m/s²]")
            self.ax_xy.plot(self.times, self.accel_x, label="Accel X [m/s²]")
            self.ax_xy.plot(self.times, self.accel_y, label="Accel Y [m/s²]")

        self.ax_alt.set_title(f"Altitude | Mode: {self.latest_mode}")
        self.ax_alt.set_xlabel("Time [s]")
        self.ax_alt.set_ylabel("Altitude [m]")
        self.ax_alt.grid(True)
        self.ax_alt.legend()

        self.ax_az.set_title("Accel Z")
        self.ax_az.set_xlabel("Time [s]")
        self.ax_az.set_ylabel("Accel Z [m/s²]")
        self.ax_az.grid(True)
        self.ax_az.legend()

        self.ax_xy.set_title("Accel X / Y")
        self.ax_xy.set_xlabel("Time [s]")
        self.ax_xy.set_ylabel("Acceleration [m/s²]")
        self.ax_xy.grid(True)
        self.ax_xy.legend()

        self.ax_status.set_title("System Status")
        self.ax_status.axis("off")

        if self.latest_frame is not None:
            lf = self.latest_frame
            status_text = self.health_status_text(lf.health_status)

            panel_text = (
                f"Mode: {lf.mode}\n"
                f"Mission Time: {lf.time_ms / 1000.0:.1f} s\n\n"
                f"IMU Valid: {lf.imu_valid}\n"
                f"Altimeter Valid: {lf.alt_valid}\n"
                f"Health Status: {status_text}\n\n"
                f"IMU Fault Count: {lf.imu_fault_count}\n"
                f"IMU Recovery Count: {lf.imu_recovery_count}\n"
                f"Alt Fault Count: {lf.alt_fault_count}\n"
                f"Alt Recovery Count: {lf.alt_recovery_count}\n\n"
                f"IMU Latched: {lf.imu_latched}\n"
                f"Alt Latched: {lf.alt_latched}\n\n"
                f"Latest Altitude: {lf.altitude_m:.2f} m\n"
                f"Latest Accel Z: {lf.az:.2f} m/s²"
            )
        else:
            panel_text = "Waiting for telemetry..."

        self.ax_status.text(
            0.03, 0.97, panel_text,
            transform=self.ax_status.transAxes,
            va="top",
            ha="left",
            fontsize=11,
            family="monospace"
        )

        self.fig.suptitle("Flight Computer Ground Station", fontsize=16)

    def run(self):
        self.start_simulator()
        self.start_reader_thread()
        self.start_csv_logging()

        self.fig = plt.figure(figsize=(14, 8))
        gs = self.fig.add_gridspec(2, 2)

        self.ax_alt = self.fig.add_subplot(gs[0, 0])
        self.ax_az = self.fig.add_subplot(gs[0, 1])
        self.ax_xy = self.fig.add_subplot(gs[1, 0])
        self.ax_status = self.fig.add_subplot(gs[1, 1])

        self.setup_buttons()

        self.anim = FuncAnimation(
            self.fig,
            self.update_dashboard,
            interval=200,
            cache_frame_data=False
        )

        try:
            plt.tight_layout(rect=[0, 0.08, 1, 1])
            plt.show()
        finally:
            self.running = False
            self.stop_csv_logging()
            if self.process and self.process.poll() is None:
                self.process.terminate()

    def start_csv_logging(self):
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = logs_dir / f"telemetry_{timestamp}.csv"

        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow([
            "time_ms",
            "mode",
            "ax",
            "ay",
            "az",
            "imu_valid",
            "altitude_m",
            "alt_valid",
            "imu_fault_count",
            "imu_recovery_count",
            "alt_fault_count",
            "alt_recovery_count",
            "imu_latched",
            "alt_latched",
            "health_status",
        ])

    def log_frame_to_csv(self, frame: TelemetryFrame):
        if self.csv_writer is None:
            return

        self.csv_writer.writerow([
            frame.time_ms,
            frame.mode,
            frame.ax,
            frame.ay,
            frame.az,
            frame.imu_valid,
            frame.altitude_m,
            frame.alt_valid,
            frame.imu_fault_count,
            frame.imu_recovery_count,
            frame.alt_fault_count,
            frame.alt_recovery_count,
            frame.imu_latched,
            frame.alt_latched,
            frame.health_status,
        ])

        self.csv_file.flush()

    def stop_csv_logging(self):
        if self.csv_file is not None:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None

    def send_command(self, cmd: str):
        if self.process is None or self.process.stdin is None:
            return

        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            print(f"[GS] Sent command: {cmd}")
        except BrokenPipeError:
            print("[GS] Cannot send command: simulator stdin is closed")

    def setup_buttons(self):
        ax_btn_reset_warn = self.fig.add_axes([0.12, 0.01, 0.12, 0.05])
        ax_btn_reset_all = self.fig.add_axes([0.26, 0.01, 0.12, 0.05])
        ax_btn_nominal = self.fig.add_axes([0.40, 0.01, 0.12, 0.05])
        ax_btn_safe = self.fig.add_axes([0.54, 0.01, 0.12, 0.05])

        self.btn_reset_warn = Button(ax_btn_reset_warn, "Reset Warn")
        self.btn_reset_all = Button(ax_btn_reset_all, "Reset All")
        self.btn_nominal = Button(ax_btn_nominal, "Force Nominal")
        self.btn_safe = Button(ax_btn_safe, "Force Safe")

        self.btn_reset_warn.on_clicked(lambda event: self.send_command("reset_warnings"))
        self.btn_reset_all.on_clicked(lambda event: self.send_command("reset_all"))
        self.btn_nominal.on_clicked(lambda event: self.send_command("force_nominal"))
        self.btn_safe.on_clicked(lambda event: self.send_command("force_safe"))

if __name__ == "__main__":
    gs = GroundStation(EXECUTABLE_PATH)
    gs.run()