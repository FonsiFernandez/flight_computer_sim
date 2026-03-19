import csv
import json
import re
import subprocess
import sys
import threading
import queue
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from collections import deque

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QLineEdit, QGroupBox,
    QMessageBox, QFrame
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


EXECUTABLE_PATH = r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software\cmake-build-debug\flight_computer_sim.exe"
REPLAY_STEP_FRAMES = 1
MAX_POINTS = 300
MAX_EVENTS = 100

LOG_LINE_PATTERN = re.compile(
    r"\[(?P<level>INFO|WARN|ERROR)\]\[T\+(?P<time>\d+)\s+ms\]\s+(?P<message>.+)"
)


@dataclass
class TelemetryFrame:
    time_ms: int
    mode: str
    mission_phase: str
    truth_time_s: float
    truth_altitude_m: float
    truth_velocity_z_mps: float
    truth_acceleration_z_mps2: float
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


class PlotWidget(FigureCanvas):
    def __init__(self):
        self.figure = Figure(facecolor="#0b0f14")
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = None
        self._setup_dark_axes()

    def _setup_dark_axes(self):
        self.ax.set_facecolor("#10161d")
        self.ax.tick_params(colors="#9fb3c8")
        for spine in self.ax.spines.values():
            spine.set_color("#3a4654")
        self.ax.title.set_color("#f5f8fb")
        self.ax.xaxis.label.set_color("#d9e2ec")
        self.ax.yaxis.label.set_color("#d9e2ec")
        self.ax.grid(True, color="#2c3846", alpha=0.35)

    def clear(self, with_secondary=False):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self._setup_dark_axes()
        self.ax2 = self.ax.twinx() if with_secondary else None
        if self.ax2 is not None:
            self.ax2.tick_params(colors="#9fb3c8")
            for spine in self.ax2.spines.values():
                spine.set_color("#3a4654")
            self.ax2.yaxis.label.set_color("#d9e2ec")

    def draw_idle_safe(self):
        self.figure.tight_layout()
        self.draw_idle()


class StatusTile(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("StatusTile")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("TileTitle")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("TileValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text: str):
        self.value_label.setText(text)

    def set_color(self, color: str):
        self.setStyleSheet(f"""
            QFrame#StatusTile {{
                background-color: #10161d;
                border: 1px solid {color};
                border-radius: 10px;
            }}
            QLabel#TileTitle {{
                color: #9fb3c8;
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#TileValue {{
                color: {color};
                font-size: 18px;
                font-weight: 700;
            }}
        """)


class GroundStationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Flight Computer Ground Station")
        self.resize(1700, 980)

        self.process = None
        self.output_queue = queue.Queue()
        self.reader_thread = None
        self.running_reader = False

        self.live_mode = False
        self.replay_mode = False
        self.replay_csv_path = None
        self.replay_frames = []
        self.replay_index = 0

        self.paused = False
        self.stopped = False

        self.csv_file = None
        self.csv_writer = None
        self.csv_path = None

        self.times = deque(maxlen=MAX_POINTS)
        self.altitudes = deque(maxlen=MAX_POINTS)
        self.truth_altitudes = deque(maxlen=MAX_POINTS)
        self.accel_x = deque(maxlen=MAX_POINTS)
        self.accel_y = deque(maxlen=MAX_POINTS)
        self.accel_z = deque(maxlen=MAX_POINTS)
        self.truth_accel_z = deque(maxlen=MAX_POINTS)
        self.altitude_error = deque(maxlen=MAX_POINTS)
        self.accel_z_error = deque(maxlen=MAX_POINTS)

        self.latest_frame = None
        self.latest_mode = "UNKNOWN"
        self.mode_transitions = []
        self.last_transition_mode = None
        self.event_lines = deque(maxlen=MAX_EVENTS)

        self._build_ui()
        self._apply_styles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(200)

    # ---------- helpers ----------

    @staticmethod
    def health_status_text(status: int):
        if status == 0:
            return "OK"
        if status == 1:
            return "WARNING"
        if status == 2:
            return "CRITICAL"
        return "UNKNOWN"

    @staticmethod
    def mode_color(mode: str):
        if mode == "NOMINAL":
            return "#33d17a"
        if mode == "DEGRADED":
            return "#ffb347"
        if mode == "SAFE":
            return "#ff5c5c"
        return "#7f8c9a"

    @staticmethod
    def health_color(status: int):
        if status == 0:
            return "#33d17a"
        if status == 1:
            return "#ffb347"
        if status == 2:
            return "#ff5c5c"
        return "#7f8c9a"

    @staticmethod
    def execution_color(text: str):
        if text == "RUNNING":
            return "#33d17a"
        if text == "PAUSED":
            return "#ffb347"
        if text == "STOPPED":
            return "#ff5c5c"
        return "#7f8c9a"

    # ---------- UI ----------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Top controls
        controls = QHBoxLayout()

        self.btn_start_live = QPushButton("Start Live")
        self.btn_open_replay = QPushButton("Open Replay")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_restart = QPushButton("Restart Replay")
        self.btn_stop = QPushButton("Stop")

        self.btn_reset_warn = QPushButton("Reset Warn")
        self.btn_reset_all = QPushButton("Reset All")
        self.btn_force_nom = QPushButton("Force Nominal")
        self.btn_force_safe = QPushButton("Force Safe")
        self.btn_status = QPushButton("Status")
        self.btn_help = QPushButton("Help")

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type manual command...")
        self.btn_send = QPushButton("Send")

        for w in [
            self.btn_start_live, self.btn_open_replay, self.btn_pause, self.btn_resume,
            self.btn_restart, self.btn_stop, self.btn_reset_warn, self.btn_reset_all,
            self.btn_force_nom, self.btn_force_safe, self.btn_status, self.btn_help
        ]:
            controls.addWidget(w)

        controls.addWidget(self.command_input, 1)
        controls.addWidget(self.btn_send)
        root.addLayout(controls)

        # Tiles
        tiles_layout = QHBoxLayout()
        self.tile_mode = StatusTile("MODE")
        self.tile_phase = StatusTile("PHASE")
        self.tile_health = StatusTile("HEALTH")
        self.tile_execution = StatusTile("EXECUTION")

        tiles_layout.addWidget(self.tile_mode)
        tiles_layout.addWidget(self.tile_phase)
        tiles_layout.addWidget(self.tile_health)
        tiles_layout.addWidget(self.tile_execution)
        root.addLayout(tiles_layout)

        # Main grid
        grid = QGridLayout()
        grid.setSpacing(10)
        root.addLayout(grid, 1)

        self.alt_plot = PlotWidget()
        self.accel_plot = PlotWidget()
        self.xy_plot = PlotWidget()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)

        self.events_text = QTextEdit()
        self.events_text.setReadOnly(True)

        grid.addWidget(self._wrap_group("Altitude / Truth vs Measured", self.alt_plot), 0, 0)
        grid.addWidget(self._wrap_group("Accel Z / Truth vs Measured", self.accel_plot), 0, 1)
        grid.addWidget(self._wrap_group("Accel X / Y", self.xy_plot), 1, 0)
        grid.addWidget(self._wrap_group("System Status", self.status_text), 1, 1)
        grid.addWidget(self._wrap_group("Event Log", self.events_text), 0, 2, 2, 1)

        self.footer_label = QLabel("Source: n/a | Mode: IDLE")
        root.addWidget(self.footer_label)

        # Signals
        self.btn_start_live.clicked.connect(self.start_live)
        self.btn_open_replay.clicked.connect(self.open_replay_file)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_resume.clicked.connect(self.resume)
        self.btn_restart.clicked.connect(self.restart_replay)
        self.btn_stop.clicked.connect(self.stop_execution)

        self.btn_reset_warn.clicked.connect(lambda: self.send_command("reset_warnings"))
        self.btn_reset_all.clicked.connect(lambda: self.send_command("reset_all"))
        self.btn_force_nom.clicked.connect(lambda: self.send_command("force_nominal"))
        self.btn_force_safe.clicked.connect(lambda: self.send_command("force_safe"))
        self.btn_status.clicked.connect(lambda: self.send_command("status"))
        self.btn_help.clicked.connect(lambda: self.send_command("help"))

        self.btn_send.clicked.connect(self.send_manual_command)
        self.command_input.returnPressed.connect(self.send_manual_command)

    def _wrap_group(self, title, widget):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0b0f14;
                color: #e6eef7;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #2a3440;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #10161d;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                color: #f5f8fb;
            }
            QPushButton {
                background-color: #17212b;
                border: 1px solid #2e3c4b;
                border-radius: 7px;
                padding: 8px 10px;
                color: #e6eef7;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #223041;
            }
            QPushButton:pressed {
                background-color: #2c4157;
            }
            QTextEdit, QLineEdit {
                background-color: #0f141a;
                border: 1px solid #2e3c4b;
                border-radius: 7px;
                color: #e6eef7;
                padding: 6px;
                font-family: Consolas, Courier New, monospace;
            }
            QLabel {
                color: #cfd9e3;
            }
        """)

    # ---------- parsing ----------

    def parse_telemetry(self, line: str):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        if data.get("type") != "telemetry":
            return None

        truth = data.get("truth", {})
        imu = data.get("imu", {})
        altimeter = data.get("altimeter", {})
        health = data.get("health", {})

        return TelemetryFrame(
            time_ms=int(data.get("time_ms", 0)),
            mode=str(data.get("mode", "UNKNOWN")),
            mission_phase=str(data.get("mission_phase", "UNKNOWN")),
            truth_time_s=float(truth.get("time_s", 0.0)),
            truth_altitude_m=float(truth.get("altitude_m", 0.0)),
            truth_velocity_z_mps=float(truth.get("velocity_z_mps", 0.0)),
            truth_acceleration_z_mps2=float(truth.get("acceleration_z_mps2", 0.0)),
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

    # ---------- state/buffers ----------

    def record_event(self, text: str):
        self.event_lines.appendleft(text)

    def record_mode_transition_if_needed(self, frame: TelemetryFrame):
        if frame.mode != self.last_transition_mode:
            transition_time_s = frame.time_ms / 1000.0
            self.mode_transitions.append((transition_time_s, frame.mode))
            self.record_event(f"T+{transition_time_s:6.1f}s | MODE -> {frame.mode}")
            self.last_transition_mode = frame.mode

    def push_telemetry_frame(self, telemetry: TelemetryFrame):
        time_s = telemetry.time_ms / 1000.0
        self.times.append(time_s)
        self.altitudes.append(telemetry.altitude_m)
        self.truth_altitudes.append(telemetry.truth_altitude_m)
        self.accel_x.append(telemetry.ax)
        self.accel_y.append(telemetry.ay)
        self.accel_z.append(telemetry.az)
        self.truth_accel_z.append(telemetry.truth_acceleration_z_mps2)
        self.altitude_error.append(telemetry.altitude_m - telemetry.truth_altitude_m)
        self.accel_z_error.append(telemetry.az - telemetry.truth_acceleration_z_mps2)
        self.latest_frame = telemetry
        self.latest_mode = telemetry.mode
        self.record_mode_transition_if_needed(telemetry)

    def reset_buffers(self):
        self.times.clear()
        self.altitudes.clear()
        self.truth_altitudes.clear()
        self.accel_x.clear()
        self.accel_y.clear()
        self.accel_z.clear()
        self.truth_accel_z.clear()
        self.altitude_error.clear()
        self.accel_z_error.clear()
        self.latest_frame = None
        self.latest_mode = "UNKNOWN"
        self.mode_transitions.clear()
        self.last_transition_mode = None
        self.event_lines.clear()

    # ---------- CSV live logging ----------

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
            "mission_phase",
            "truth_time_s",
            "truth_altitude_m",
            "truth_velocity_z_mps",
            "truth_acceleration_z_mps2",
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
            frame.mission_phase,
            frame.truth_time_s,
            frame.truth_altitude_m,
            frame.truth_velocity_z_mps,
            frame.truth_acceleration_z_mps2,
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

    # ---------- live ----------

    def start_live(self):
        self.stop_process_if_running()
        self.reset_buffers()

        self.live_mode = True
        self.replay_mode = False
        self.paused = False
        self.stopped = False

        try:
            self.process = subprocess.Popen(
                [EXECUTABLE_PATH],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"Executable not found:\n{EXECUTABLE_PATH}")
            return

        self.start_csv_logging()
        self.running_reader = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

        self.record_event("LIVE      | simulator started")

    def _reader_loop(self):
        if self.process is None or self.process.stdout is None:
            return

        while self.running_reader:
            line = self.process.stdout.readline()
            if not line:
                break
            self.output_queue.put(line.strip())

    def consume_live_output(self):
        if self.stopped or self.paused:
            return

        while not self.output_queue.empty():
            line = self.output_queue.get()

            log_data = self.parse_log_line(line)
            if log_data is not None:
                event_text = f"T+{log_data['time_ms'] / 1000.0:6.1f}s | {log_data['level']:5s} | {log_data['message']}"
                self.record_event(event_text)

            telemetry = self.parse_telemetry(line)
            if telemetry is None:
                continue

            self.push_telemetry_frame(telemetry)
            self.log_frame_to_csv(telemetry)

    def stop_process_if_running(self):
        self.running_reader = False
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.process = None
        self.stop_csv_logging()

    # ---------- replay ----------

    def open_replay_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select replay CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            self.record_event("REPLAY    | file selection cancelled")
            return

        self.stop_process_if_running()
        self.reset_buffers()

        self.live_mode = False
        self.replay_mode = True
        self.replay_csv_path = file_path
        self.replay_frames.clear()
        self.replay_index = 0
        self.paused = False
        self.stopped = False

        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.replay_frames.append(
                    TelemetryFrame(
                        time_ms=int(row["time_ms"]),
                        mode=row["mode"],
                        mission_phase=row.get("mission_phase", "UNKNOWN"),
                        truth_time_s=float(row.get("truth_time_s", 0.0)),
                        truth_altitude_m=float(row.get("truth_altitude_m", 0.0)),
                        truth_velocity_z_mps=float(row.get("truth_velocity_z_mps", 0.0)),
                        truth_acceleration_z_mps2=float(row.get("truth_acceleration_z_mps2", 0.0)),
                        ax=float(row["ax"]),
                        ay=float(row["ay"]),
                        az=float(row["az"]),
                        imu_valid=int(row["imu_valid"]),
                        altitude_m=float(row["altitude_m"]),
                        alt_valid=int(row["alt_valid"]),
                        imu_fault_count=int(row["imu_fault_count"]),
                        imu_recovery_count=int(row["imu_recovery_count"]),
                        alt_fault_count=int(row["alt_fault_count"]),
                        alt_recovery_count=int(row["alt_recovery_count"]),
                        imu_latched=int(row["imu_latched"]),
                        alt_latched=int(row["alt_latched"]),
                        health_status=int(row["health_status"]),
                    )
                )

        self.record_event(f"REPLAY    | loaded file: {file_path}")

    def consume_replay_frames(self):
        if self.stopped or self.paused:
            return
        if self.replay_index >= len(self.replay_frames):
            return

        for _ in range(REPLAY_STEP_FRAMES):
            if self.replay_index >= len(self.replay_frames):
                break
            telemetry = self.replay_frames[self.replay_index]
            self.replay_index += 1
            self.push_telemetry_frame(telemetry)

    def restart_replay(self):
        if not self.replay_mode:
            self.record_event("OPERATOR  | restart ignored (not in replay mode)")
            return
        self.replay_index = 0
        self.paused = False
        self.stopped = False
        self.reset_buffers()
        self.record_event("REPLAY    | restarted")

    # ---------- controls ----------

    def pause(self):
        self.paused = True
        self.record_event("OPERATOR  | paused")

    def resume(self):
        if self.stopped:
            self.record_event("OPERATOR  | resume ignored after stop")
            return
        self.paused = False
        self.record_event("OPERATOR  | resumed")

    def stop_execution(self):
        self.stopped = True
        self.paused = True
        self.record_event("OPERATOR  | stopped acquisition/simulation")
        if self.live_mode:
            self.stop_process_if_running()

    def send_command(self, cmd: str):
        cmd = cmd.strip()
        if not cmd:
            return

        if self.stopped:
            self.record_event(f"OPERATOR  | command ignored after stop: {cmd}")
            return

        if self.replay_mode:
            self.record_event(f"REPLAY    | command ignored in replay mode: {cmd}")
            return

        if self.process is None or self.process.stdin is None:
            return

        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            self.record_event(f"OPERATOR  | sent command: {cmd}")
        except BrokenPipeError:
            self.record_event("OPERATOR  | failed to send command: stdin closed")

    def send_manual_command(self):
        cmd = self.command_input.text().strip()
        if cmd:
            self.send_command(cmd)
            self.command_input.clear()

    # ---------- rendering ----------

    def update_dashboard(self):
        if self.replay_mode:
            self.consume_replay_frames()
        elif self.live_mode:
            self.consume_live_output()

        self.render_tiles()
        self.render_plots()
        self.render_status()
        self.render_events()

        source = self.replay_csv_path if self.replay_mode else (self.csv_path.name if self.csv_path else "n/a")
        mode_label = "REPLAY" if self.replay_mode else ("LIVE" if self.live_mode else "IDLE")
        self.footer_label.setText(f"Source: {source} | Session: {mode_label} | Current mode: {self.latest_mode}")

    def render_tiles(self):
        if self.latest_frame is None:
            self.tile_mode.set_value("--")
            self.tile_phase.set_value("--")
            self.tile_health.set_value("--")
            self.tile_execution.set_value("IDLE")
            for tile in [self.tile_mode, self.tile_phase, self.tile_health, self.tile_execution]:
                tile.set_color("#7f8c9a")
            return

        lf = self.latest_frame
        execution_state = "STOPPED" if self.stopped else ("PAUSED" if self.paused else "RUNNING")
        health_text = self.health_status_text(lf.health_status)

        self.tile_mode.set_value(lf.mode)
        self.tile_phase.set_value(lf.mission_phase)
        self.tile_health.set_value(health_text)
        self.tile_execution.set_value(execution_state)

        self.tile_mode.set_color(self.mode_color(lf.mode))
        self.tile_phase.set_color("#7fb3ff")
        self.tile_health.set_color(self.health_color(lf.health_status))
        self.tile_execution.set_color(self.execution_color(execution_state))

    def render_plots(self):
        # Altitude
        self.alt_plot.clear(with_secondary=True)
        self.alt_plot.ax.set_title("ALTITUDE / TRUTH VS MEASURED")
        self.alt_plot.ax.set_xlabel("Time [s]")
        self.alt_plot.ax.set_ylabel("Altitude [m]")
        self.alt_plot.ax2.set_ylabel("Altitude Error [m]")

        if len(self.times) > 0:
            self.alt_plot.ax.plot(self.times, self.altitudes, linewidth=2.0, label="Measured Altitude")
            self.alt_plot.ax.plot(self.times, self.truth_altitudes, linewidth=1.8, linestyle="--", label="Truth Altitude")
            self.alt_plot.ax2.plot(self.times, self.altitude_error, linewidth=1.3, linestyle=":", label="Altitude Error")

        alt_lines, alt_labels = self.alt_plot.ax.get_legend_handles_labels()
        alt2_lines, alt2_labels = self.alt_plot.ax2.get_legend_handles_labels()
        self.alt_plot.ax.legend(alt_lines + alt2_lines, alt_labels + alt2_labels, loc="upper left", fontsize=8)
        self.alt_plot.draw_idle_safe()

        # Accel Z
        self.accel_plot.clear(with_secondary=True)
        self.accel_plot.ax.set_title("ACCEL Z / TRUTH VS MEASURED")
        self.accel_plot.ax.set_xlabel("Time [s]")
        self.accel_plot.ax.set_ylabel("Accel Z [m/s²]")
        self.accel_plot.ax2.set_ylabel("Accel Error [m/s²]")

        if len(self.times) > 0:
            self.accel_plot.ax.plot(self.times, self.accel_z, linewidth=2.0, label="Measured Accel Z")
            self.accel_plot.ax.plot(self.times, self.truth_accel_z, linewidth=1.8, linestyle="--", label="Truth Accel Z")
            self.accel_plot.ax2.plot(self.times, self.accel_z_error, linewidth=1.3, linestyle=":", label="Accel Error")

        az_lines, az_labels = self.accel_plot.ax.get_legend_handles_labels()
        az2_lines, az2_labels = self.accel_plot.ax2.get_legend_handles_labels()
        self.accel_plot.ax.legend(az_lines + az2_lines, az_labels + az2_labels, loc="upper left", fontsize=8)
        self.accel_plot.draw_idle_safe()

        # Accel X/Y
        self.xy_plot.clear(with_secondary=False)
        self.xy_plot.ax.set_title("ACCEL X / Y")
        self.xy_plot.ax.set_xlabel("Time [s]")
        self.xy_plot.ax.set_ylabel("Acceleration [m/s²]")

        if len(self.times) > 0:
            self.xy_plot.ax.plot(self.times, self.accel_x, linewidth=1.8, label="Accel X")
            self.xy_plot.ax.plot(self.times, self.accel_y, linewidth=1.8, label="Accel Y")

        self.xy_plot.ax.legend(loc="upper left", fontsize=8)
        self.xy_plot.draw_idle_safe()

    def render_status(self):
        if self.latest_frame is None:
            self.status_text.setPlainText("WAITING FOR TELEMETRY...")
            return

        lf = self.latest_frame
        status_text = self.health_status_text(lf.health_status)
        execution_state = "STOPPED" if self.stopped else ("PAUSED" if self.paused else "RUNNING")
        replay_label = f"{self.replay_index}/{len(self.replay_frames)}" if self.replay_mode else "LIVE"

        panel_text = (
            f"MODE:            {lf.mode}\n"
            f"EXECUTION:       {execution_state}\n"
            f"PHASE:           {lf.mission_phase}\n"
            f"TIME:            {lf.time_ms / 1000.0:.1f} s\n\n"
            f"TRUTH ALT:       {lf.truth_altitude_m:.2f} m\n"
            f"TRUTH VEL Z:     {lf.truth_velocity_z_mps:.2f} m/s\n"
            f"TRUTH ACCEL Z:   {lf.truth_acceleration_z_mps2:.2f} m/s²\n\n"
            f"MEAS ALT:        {lf.altitude_m:.2f} m\n"
            f"MEAS ACCEL Z:    {lf.az:.2f} m/s²\n"
            f"ALT ERROR:       {lf.altitude_m - lf.truth_altitude_m:.2f} m\n"
            f"ACCEL ERROR:     {lf.az - lf.truth_acceleration_z_mps2:.2f} m/s²\n\n"
            f"IMU VALID:       {lf.imu_valid}\n"
            f"ALT VALID:       {lf.alt_valid}\n"
            f"HEALTH:          {status_text}\n\n"
            f"IMU FAULT CNT:   {lf.imu_fault_count}\n"
            f"IMU REC CNT:     {lf.imu_recovery_count}\n"
            f"ALT FAULT CNT:   {lf.alt_fault_count}\n"
            f"ALT REC CNT:     {lf.alt_recovery_count}\n\n"
            f"IMU LATCHED:     {lf.imu_latched}\n"
            f"ALT LATCHED:     {lf.alt_latched}\n\n"
            f"REPLAY FRAME:    {replay_label}"
        )

        self.status_text.setPlainText(panel_text)

    def render_events(self):
        if len(self.event_lines) == 0:
            self.events_text.setPlainText("WAITING FOR EVENTS...")
        else:
            self.events_text.setPlainText("\n".join(self.event_lines))

    # ---------- lifecycle ----------

    def closeEvent(self, event):
        self.stop_process_if_running()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GroundStationWindow()
    window.show()
    sys.exit(app.exec())