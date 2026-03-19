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

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QLineEdit, QGroupBox,
    QMessageBox, QFrame
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


DEFAULT_EXECUTABLE_PATH = r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software\cmake-build-debug\flight_computer_sim.exe"
REPLAY_STEP_FRAMES = 1
MAX_POINTS = 300
MAX_EVENTS = 200

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
    truth_pitch_deg: float
    truth_pitch_rate_dps: float
    ax: float
    ay: float
    az: float
    gyro_z_dps: float
    imu_valid: int
    altitude_m: float
    alt_valid: int
    gps_altitude_m: float
    gps_velocity_z_mps: float
    gps_fix_valid: int
    battery_voltage_v: float
    board_temp_c: float
    hk_valid: int
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

        self.gps_altitudes = deque(maxlen=MAX_POINTS)
        self.battery_voltage = deque(maxlen=MAX_POINTS)
        self.board_temp = deque(maxlen=MAX_POINTS)
        self.gyro_z = deque(maxlen=MAX_POINTS)

        self.setWindowTitle("Flight Computer Ground Station")
        self.resize(1760, 1000)

        self.executable_path = DEFAULT_EXECUTABLE_PATH
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

        self.event_log_file = None
        self.event_log_path = None

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

        controls = QHBoxLayout()

        self.btn_select_exe = QPushButton("Select EXE")
        self.btn_start_live = QPushButton("Start Live")
        self.btn_open_replay = QPushButton("Open Replay")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_restart = QPushButton("Restart Replay")
        self.btn_stop = QPushButton("Stop")
        self.btn_screenshot = QPushButton("Screenshot")

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
            self.btn_select_exe, self.btn_start_live, self.btn_open_replay,
            self.btn_pause, self.btn_resume, self.btn_restart, self.btn_stop,
            self.btn_screenshot, self.btn_reset_warn, self.btn_reset_all,
            self.btn_force_nom, self.btn_force_safe, self.btn_status, self.btn_help
        ]:
            controls.addWidget(w)

        controls.addWidget(self.command_input, 1)
        controls.addWidget(self.btn_send)
        root.addLayout(controls)

        tiles_layout = QHBoxLayout()
        self.tile_mode = StatusTile("MODE")
        self.tile_phase = StatusTile("PHASE")
        self.tile_health = StatusTile("HEALTH")
        self.tile_execution = StatusTile("EXECUTION")
        self.tile_gps = StatusTile("GPS FIX")
        self.tile_battery = StatusTile("BATTERY")
        self.tile_temp = StatusTile("TEMP")

        tiles_layout.addWidget(self.tile_gps)
        tiles_layout.addWidget(self.tile_battery)
        tiles_layout.addWidget(self.tile_temp)
        tiles_layout.addWidget(self.tile_mode)
        tiles_layout.addWidget(self.tile_phase)
        tiles_layout.addWidget(self.tile_health)
        tiles_layout.addWidget(self.tile_execution)
        root.addLayout(tiles_layout)

        grid = QGridLayout()
        grid.setSpacing(10)
        root.addLayout(grid, 1)

        self.alt_plot = PlotWidget()
        self.accel_plot = PlotWidget()
        self.xy_plot = PlotWidget()
        self.hk_plot = PlotWidget();

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)

        self.events_text = QTextEdit()
        self.events_text.setReadOnly(True)

        grid.addWidget(self._wrap_group("Altitude / Truth vs Measured", self.alt_plot), 0, 0)
        grid.addWidget(self._wrap_group("Accel Z / Truth vs Measured", self.accel_plot), 0, 1)
        grid.addWidget(self._wrap_group("Accel X / Y", self.xy_plot), 1, 0)
        grid.addWidget(self._wrap_group("Battery / Temperature", self.hk_plot), 1, 1)
        grid.addWidget(self._wrap_group("System Status", self.status_text), 0, 2)
        grid.addWidget(self._wrap_group("Event Log", self.events_text), 1, 2)

        self.footer_label = QLabel("Source: n/a | Session: IDLE | Current mode: UNKNOWN")
        root.addWidget(self.footer_label)

        self.btn_select_exe.clicked.connect(self.select_executable)
        self.btn_start_live.clicked.connect(self.start_live)
        self.btn_open_replay.clicked.connect(self.open_replay_file)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_resume.clicked.connect(self.resume)
        self.btn_restart.clicked.connect(self.restart_replay)
        self.btn_stop.clicked.connect(self.stop_execution)
        self.btn_screenshot.clicked.connect(self.save_screenshot)

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
        gps = data.get("gps", {})
        hk = data.get("hk", {})
        health = data.get("health", {})

        return TelemetryFrame(
            time_ms=int(data.get("time_ms", 0)),
            mode=str(data.get("mode", "UNKNOWN")),
            mission_phase=str(data.get("mission_phase", "UNKNOWN")),

            truth_time_s=float(truth.get("time_s", 0.0)),
            truth_altitude_m=float(truth.get("altitude_m", 0.0)),
            truth_velocity_z_mps=float(truth.get("velocity_z_mps", 0.0)),
            truth_acceleration_z_mps2=float(truth.get("acceleration_z_mps2", 0.0)),
            truth_pitch_deg=float(truth.get("pitch_deg", 0.0)),
            truth_pitch_rate_dps=float(truth.get("pitch_rate_dps", 0.0)),

            ax=float(imu.get("x", 0.0)),
            ay=float(imu.get("y", 0.0)),
            az=float(imu.get("z", 0.0)),
            gyro_z_dps=float(imu.get("gyro_z_dps", 0.0)),
            imu_valid=int(imu.get("valid", 0)),

            altitude_m=float(altimeter.get("altitude_m", 0.0)),
            alt_valid=int(altimeter.get("valid", 0)),

            gps_altitude_m=float(gps.get("altitude_m", 0.0)),
            gps_velocity_z_mps=float(gps.get("velocity_z_mps", 0.0)),
            gps_fix_valid=int(gps.get("fix_valid", 0)),

            battery_voltage_v=float(hk.get("battery_voltage_v", 0.0)),
            board_temp_c=float(hk.get("board_temp_c", 0.0)),
            hk_valid=int(hk.get("valid", 0)),

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

    def start_event_logging(self, source_name: str):
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_source = source_name.replace("\\", "_").replace("/", "_").replace(":", "_")
        self.event_log_path = logs_dir / f"events_{timestamp}_{safe_source}.log"
        self.event_log_file = open(self.event_log_path, "w", encoding="utf-8")

    def stop_event_logging(self):
        if self.event_log_file is not None:
            self.event_log_file.close()
            self.event_log_file = None
            self.event_log_path = None

    def record_event(self, text: str):
        self.event_lines.appendleft(text)
        if self.event_log_file is not None:
            self.event_log_file.write(text + "\n")
            self.event_log_file.flush()

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
        self.gps_altitudes.append(telemetry.gps_altitude_m)
        self.battery_voltage.append(telemetry.battery_voltage_v)
        self.board_temp.append(telemetry.board_temp_c)
        self.gyro_z.append(telemetry.gyro_z_dps)

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
        self.gps_altitudes.clear()
        self.battery_voltage.clear()
        self.board_temp.clear()
        self.gyro_z.clear()
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
            "truth_pitch_deg",
            "truth_pitch_rate_dps",
            "ax",
            "ay",
            "az",
            "gyro_z_dps",
            "imu_valid",
            "altitude_m",
            "alt_valid",
            "gps_altitude_m",
            "gps_velocity_z_mps",
            "gps_fix_valid",
            "battery_voltage_v",
            "board_temp_c",
            "hk_valid",
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
            frame.truth_pitch_deg,
            frame.truth_pitch_rate_dps,
            frame.ax,
            frame.ay,
            frame.az,
            frame.gyro_z_dps,
            frame.imu_valid,
            frame.altitude_m,
            frame.alt_valid,
            frame.gps_altitude_m,
            frame.gps_velocity_z_mps,
            frame.gps_fix_valid,
            frame.battery_voltage_v,
            frame.board_temp_c,
            frame.hk_valid,
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
            self.csv_path = None

    # ---------- live ----------

    def select_executable(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select simulator executable",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.executable_path = file_path
            self.record_event(f"LIVE      | executable selected: {file_path}")

    def start_live(self):
        self.stop_process_if_running()
        self.reset_buffers()

        self.live_mode = True
        self.replay_mode = False
        self.paused = False
        self.stopped = False

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
            QMessageBox.critical(self, "Error", f"Executable not found:\n{self.executable_path}")
            return

        self.start_csv_logging()
        self.start_event_logging("live")
        self.running_reader = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

        self.record_event(f"LIVE      | simulator started: {self.executable_path}")

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
        self.stop_event_logging()

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

        self.start_event_logging("replay")
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

    def save_screenshot(self):
        out_dir = Path("logs")
        out_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"screenshot_{timestamp}.png"
        self.grab().save(str(out_path))
        self.record_event(f"OPERATOR  | screenshot saved: {out_path}")

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

    def draw_transition_lines(self, plot_widget):
        if not self.mode_transitions:
            return
        for t_s, mode in self.mode_transitions:
            color = self.mode_color(mode)
            plot_widget.ax.axvline(t_s, color=color, linestyle="--", linewidth=1.0, alpha=0.55)

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
        session = "REPLAY" if self.replay_mode else ("LIVE" if self.live_mode else "IDLE")
        self.footer_label.setText(f"Source: {source} | Session: {session} | Current mode: {self.latest_mode}")

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

        gps_text = "OK" if lf.gps_fix_valid else "NO FIX"
        self.tile_gps.set_value(gps_text)
        self.tile_gps.set_color("#33d17a" if lf.gps_fix_valid else "#ff5c5c")

        self.tile_battery.set_value(f"{lf.battery_voltage_v:.2f} V")
        self.tile_battery.set_color("#33d17a" if lf.battery_voltage_v > 14 else "#ffb347")

        self.tile_temp.set_value(f"{lf.board_temp_c:.1f} °C")
        self.tile_temp.set_color("#33d17a" if lf.board_temp_c < 50 else "#ff5c5c")

    def render_plots(self):
        # Altitude
        self.alt_plot.clear(with_secondary=True)
        self.alt_plot.ax.set_title("ALTITUDE / TRUTH VS MEASURED")
        self.alt_plot.ax.set_xlabel("Time [s]")
        self.alt_plot.ax.set_ylabel("Altitude [m]")
        self.alt_plot.ax2.set_ylabel("Altitude Error [m]")

        if len(self.times) > 0:
            self.alt_plot.ax.plot(self.times, self.altitudes, linewidth=2.0, label="Measured Altitude")
            self.alt_plot.ax.plot(self.times, self.truth_altitudes, linewidth=1.8, linestyle="--",
                                  label="Truth Altitude")
            self.alt_plot.ax.plot(self.times, self.gps_altitudes, linewidth=1.5, linestyle=":", label="GPS Altitude")
            self.alt_plot.ax2.plot(self.times, self.altitude_error, linewidth=1.3, linestyle=":",
                                   label="Altitude Error")

        self.draw_transition_lines(self.alt_plot)

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
            self.accel_plot.ax.plot(self.times, self.truth_accel_z, linewidth=1.8, linestyle="--",
                                    label="Truth Accel Z")
            self.accel_plot.ax2.plot(self.times, self.accel_z_error, linewidth=1.3, linestyle=":", label="Accel Error")

        self.draw_transition_lines(self.accel_plot)

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
            self.xy_plot.ax.plot(self.times, self.gyro_z, linewidth=1.4, linestyle="--", label="Gyro Z [dps]")

        self.draw_transition_lines(self.xy_plot)

        handles, labels = self.xy_plot.ax.get_legend_handles_labels()
        if handles:
            self.xy_plot.ax.legend(loc="upper left", fontsize=8)
        self.xy_plot.draw_idle_safe()

        # Battery / Temperature
        self.hk_plot.clear(with_secondary=True)
        self.hk_plot.ax.set_title("BATTERY / TEMPERATURE")
        self.hk_plot.ax.set_xlabel("Time [s]")
        self.hk_plot.ax.set_ylabel("Battery [V]")
        self.hk_plot.ax2.set_ylabel("Temperature [°C]")

        if len(self.times) > 0:
            self.hk_plot.ax.plot(self.times, self.battery_voltage, linewidth=1.8, label="Battery [V]")
            self.hk_plot.ax2.plot(self.times, self.board_temp, linewidth=1.8, linestyle="--", label="Temp [°C]")

        self.draw_transition_lines(self.hk_plot)

        h1, l1 = self.hk_plot.ax.get_legend_handles_labels()
        h2, l2 = self.hk_plot.ax2.get_legend_handles_labels()
        if h1 or h2:
            self.hk_plot.ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
        self.hk_plot.draw_idle_safe()

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
            f"TRUTH ACCEL Z:   {lf.truth_acceleration_z_mps2:.2f} m/s²\n"
            f"TRUTH PITCH:     {lf.truth_pitch_deg:.2f} deg\n"
            f"TRUTH PITCH RT:  {lf.truth_pitch_rate_dps:.2f} dps\n\n"

            f"MEAS ALT:        {lf.altitude_m:.2f} m\n"
            f"GPS ALT:         {lf.gps_altitude_m:.2f} m\n"
            f"GPS VEL Z:       {lf.gps_velocity_z_mps:.2f} m/s\n"
            f"MEAS ACCEL Z:    {lf.az:.2f} m/s²\n"
            f"GYRO Z:          {lf.gyro_z_dps:.2f} dps\n"
            f"ALT ERROR:       {lf.altitude_m - lf.truth_altitude_m:.2f} m\n"
            f"ACCEL ERROR:     {lf.az - lf.truth_acceleration_z_mps2:.2f} m/s²\n\n"

            f"BATTERY:         {lf.battery_voltage_v:.2f} V\n"
            f"TEMP:            {lf.board_temp_c:.2f} °C\n"
            f"HK VALID:        {lf.hk_valid}\n\n"

            f"IMU VALID:       {lf.imu_valid}\n"
            f"ALT VALID:       {lf.alt_valid}\n"
            f"GPS FIX:         {lf.gps_fix_valid}\n"
            f"HEALTH:          {status_text}\n\n"

            f"IMU FAULT CNT:   {lf.imu_fault_count}\n"
            f"IMU REC CNT:     {lf.imu_recovery_count}\n"
            f"ALT FAULT CNT:   {lf.alt_fault_count}\n"
            f"ALT REC CNT:     {lf.alt_recovery_count}\n\n"

            f"IMU LATCHED:     {lf.imu_latched}\n"
            f"ALT LATCHED:     {lf.alt_latched}\n\n"

            f"REPLAY FRAME:    {replay_label}\n"
            f"EVENT LOG FILE:  {self.event_log_path.name if self.event_log_path else 'n/a'}\n"
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