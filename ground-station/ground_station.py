import subprocess
import sys
import re
import threading
import queue
import csv
import json
from pathlib import Path
from datetime import datetime
from collections import deque
from dataclasses import dataclass

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox

EXECUTABLE_PATH = r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software\cmake-build-debug\flight_computer_sim.exe"

LOG_LINE_PATTERN = re.compile(
    r"\[(?P<level>INFO|WARN|ERROR)\]\[T\+(?P<time>\d+)\s+ms\]\s+(?P<message>.+)"
)

MAX_POINTS = 300
MAX_EVENTS = 14


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

        self.event_lines = deque(maxlen=MAX_EVENTS)
        self.mode_transitions = []
        self.last_transition_mode = None

        self.fig = None
        self.ax_alt = None
        self.ax_az = None
        self.ax_xy = None
        self.ax_status = None
        self.ax_events = None

        self.btn_reset_warn = None
        self.btn_reset_all = None
        self.btn_nominal = None
        self.btn_safe = None
        self.btn_status = None
        self.btn_help = None
        self.command_box = None
        self.btn_send = None

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
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        if data.get("type") != "telemetry":
            return None

        imu = data.get("imu", {})
        altimeter = data.get("altimeter", {})
        health = data.get("health", {})

        return TelemetryFrame(
            time_ms=int(data.get("time_ms", 0)),
            mode=str(data.get("mode", "UNKNOWN")),
            ax=float(imu.get("x", 0.0)),
            ay=float(imu.get("y", 0.0)),
            az=float(imu.get("z", 0.0)),
            imu_valid=int(imu.get("valid", 0)),
            altitude_m=float(altimeter.get("altitude_m", 0.0)),
            alt_valid=int(altimeter.get("valid", 0)),
            imu_fault_count=int(health.get("imu_fault_count", 0)),
            imu_recovery_count=int(health.get("imu_recovery_count", 0)),
            alt_fault_count=int(health.get("alt_fault_count", 0)),
            alt_recovery_count=int(health.get("alt_recovery_count", 0)),
            imu_latched=int(health.get("imu_latched", 0)),
            alt_latched=int(health.get("alt_latched", 0)),
            health_status=int(health.get("status", 0)),
        )

    def parse_log_line(self, line: str):
        match = LOG_LINE_PATTERN.search(line)
        if not match:
            return None

        return {
            "level": match.group("level"),
            "time_ms": int(match.group("time")),
            "message": match.group("message"),
        }

    def record_event(self, text: str):
        self.event_lines.appendleft(text)

    def record_mode_transition_if_needed(self, frame: TelemetryFrame):
        if frame.mode != self.last_transition_mode:
            transition_time_s = frame.time_ms / 1000.0
            self.mode_transitions.append((transition_time_s, frame.mode))
            self.record_event(f"T+{transition_time_s:6.1f}s | MODE -> {frame.mode}")
            self.last_transition_mode = frame.mode

    def consume_available_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get()
            print(f"[SIM] {line}")

            log_data = self.parse_log_line(line)
            if log_data is not None:
                event_text = f"T+{log_data['time_ms'] / 1000.0:6.1f}s | {log_data['level']:5s} | {log_data['message']}"
                self.record_event(event_text)

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

            self.record_mode_transition_if_needed(telemetry)
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
    def mode_line_color(mode: str):
        if mode == "NOMINAL":
            return "green"
        if mode == "DEGRADED":
            return "orange"
        if mode == "SAFE":
            return "red"
        return "gray"

    @staticmethod
    def health_status_text(status: int):
        if status == 0:
            return "OK"
        if status == 1:
            return "WARNING"
        if status == 2:
            return "CRITICAL"
        return "UNKNOWN"

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

        cmd = cmd.strip()
        if not cmd:
            return

        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            self.record_event(f"OPERATOR  | sent command: {cmd}")
            print(f"[GS] Sent command: {cmd}")
        except BrokenPipeError:
            self.record_event("OPERATOR  | failed to send command: stdin closed")
            print("[GS] Cannot send command: simulator stdin is closed")

    def on_send_command(self, _event):
        if self.command_box is None:
            return
        cmd = self.command_box.text.strip()
        if cmd:
            self.send_command(cmd)
            self.command_box.set_val("")

    def on_submit_command(self, text):
        cmd = text.strip()
        if cmd:
            self.send_command(cmd)
            self.command_box.set_val("")

    def setup_buttons(self):
        ax_btn_reset_warn = self.fig.add_axes([0.07, 0.02, 0.11, 0.045])
        ax_btn_reset_all = self.fig.add_axes([0.19, 0.02, 0.11, 0.045])
        ax_btn_nominal = self.fig.add_axes([0.31, 0.02, 0.11, 0.045])
        ax_btn_safe = self.fig.add_axes([0.43, 0.02, 0.11, 0.045])
        ax_btn_status = self.fig.add_axes([0.55, 0.02, 0.09, 0.045])
        ax_btn_help = self.fig.add_axes([0.65, 0.02, 0.08, 0.045])

        ax_textbox = self.fig.add_axes([0.75, 0.02, 0.15, 0.045])
        ax_btn_send = self.fig.add_axes([0.91, 0.02, 0.06, 0.045])

        self.btn_reset_warn = Button(ax_btn_reset_warn, "Reset Warn")
        self.btn_reset_all = Button(ax_btn_reset_all, "Reset All")
        self.btn_nominal = Button(ax_btn_nominal, "Force Nom")
        self.btn_safe = Button(ax_btn_safe, "Force Safe")
        self.btn_status = Button(ax_btn_status, "Status")
        self.btn_help = Button(ax_btn_help, "Help")

        self.command_box = TextBox(ax_textbox, "", initial="")
        self.btn_send = Button(ax_btn_send, "Send")

        self.btn_reset_warn.on_clicked(lambda event: self.send_command("reset_warnings"))
        self.btn_reset_all.on_clicked(lambda event: self.send_command("reset_all"))
        self.btn_nominal.on_clicked(lambda event: self.send_command("force_nominal"))
        self.btn_safe.on_clicked(lambda event: self.send_command("force_safe"))
        self.btn_status.on_clicked(lambda event: self.send_command("status"))
        self.btn_help.on_clicked(lambda event: self.send_command("help"))

        self.btn_send.on_clicked(self.on_send_command)
        self.command_box.on_submit(self.on_submit_command)

    def draw_mode_transition_lines(self):
        for t_s, mode in self.mode_transitions:
            color = self.mode_line_color(mode)
            self.ax_alt.axvline(t_s, linestyle="--", linewidth=1.0, color=color, alpha=0.65)
            self.ax_az.axvline(t_s, linestyle="--", linewidth=1.0, color=color, alpha=0.65)
            self.ax_xy.axvline(t_s, linestyle="--", linewidth=1.0, color=color, alpha=0.65)

    def update_dashboard(self, _frame):
        self.consume_available_output()

        self.ax_alt.clear()
        self.ax_az.clear()
        self.ax_xy.clear()
        self.ax_status.clear()
        self.ax_events.clear()

        bg_color = self.mode_color(self.latest_mode)

        self.ax_alt.set_facecolor(bg_color)
        self.ax_az.set_facecolor(bg_color)
        self.ax_xy.set_facecolor(bg_color)
        self.ax_status.set_facecolor(bg_color)
        self.ax_events.set_facecolor("#f7f7f7")

        if len(self.times) > 0:
            self.ax_alt.plot(self.times, self.altitudes, label="Altitude [m]")
            self.ax_az.plot(self.times, self.accel_z, label="Accel Z [m/s²]")
            self.ax_xy.plot(self.times, self.accel_x, label="Accel X [m/s²]")
            self.ax_xy.plot(self.times, self.accel_y, label="Accel Y [m/s²]")

        self.draw_mode_transition_lines()

        self.ax_alt.set_title(f"Altitude | Mode: {self.latest_mode}")
        self.ax_alt.set_xlabel("Time [s]")
        self.ax_alt.set_ylabel("Altitude [m]")
        self.ax_alt.grid(True)
        self.ax_alt.legend(loc="upper left")

        self.ax_az.set_title("Accel Z")
        self.ax_az.set_xlabel("Time [s]")
        self.ax_az.set_ylabel("Accel Z [m/s²]")
        self.ax_az.grid(True)
        self.ax_az.legend(loc="upper left")

        self.ax_xy.set_title("Accel X / Y")
        self.ax_xy.set_xlabel("Time [s]")
        self.ax_xy.set_ylabel("Acceleration [m/s²]")
        self.ax_xy.grid(True)
        self.ax_xy.legend(loc="upper left")

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
                f"Latest Accel Z: {lf.az:.2f} m/s²\n\n"
                f"CSV: {self.csv_path.name if self.csv_path else 'n/a'}"
            )
        else:
            panel_text = "Waiting for telemetry..."

        self.ax_status.text(
            0.03, 0.97, panel_text,
            transform=self.ax_status.transAxes,
            va="top",
            ha="left",
            fontsize=10.5,
            family="monospace"
        )

        self.ax_events.set_title("Event Log")
        self.ax_events.axis("off")

        if len(self.event_lines) == 0:
            event_text = "Waiting for events..."
        else:
            event_text = "\n".join(self.event_lines)

        self.ax_events.text(
            0.02, 0.98, event_text,
            transform=self.ax_events.transAxes,
            va="top",
            ha="left",
            fontsize=9.5,
            family="monospace"
        )

        self.fig.suptitle("Flight Computer Ground Station", fontsize=16)

    def run(self):
        self.start_simulator()
        self.start_reader_thread()
        self.start_csv_logging()

        self.fig = plt.figure(figsize=(15, 9))
        gs = self.fig.add_gridspec(2, 3)

        self.ax_alt = self.fig.add_subplot(gs[0, 0])
        self.ax_az = self.fig.add_subplot(gs[0, 1])
        self.ax_xy = self.fig.add_subplot(gs[1, 0])
        self.ax_status = self.fig.add_subplot(gs[1, 1])
        self.ax_events = self.fig.add_subplot(gs[:, 2])

        self.setup_buttons()

        self.anim = FuncAnimation(
            self.fig,
            self.update_dashboard,
            interval=200,
            cache_frame_data=False
        )

        try:
            self.fig.subplots_adjust(left=0.05, right=0.98, top=0.92, bottom=0.12, wspace=0.28, hspace=0.30)
            plt.show()
        finally:
            self.running = False
            self.stop_csv_logging()
            if self.process and self.process.poll() is None:
                self.process.terminate()


if __name__ == "__main__":
    gs = GroundStation(EXECUTABLE_PATH)
    gs.run()