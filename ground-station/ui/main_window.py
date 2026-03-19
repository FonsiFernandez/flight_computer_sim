import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QLineEdit, QGroupBox,
    QMessageBox, QToolButton
)

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from parsing.telemetry_parser import TelemetryParser
from parsing.log_parser import LogParser
from services.csv_logger import CsvTelemetryLogger
from services.event_logger import EventLogger
from services.live_session import LiveSession
from services.replay_session import ReplaySession
from state.telemetry_buffer import TelemetryBuffer
from ui.widgets.plot_widget import PlotWidget
from ui.widgets.status_tile import StatusTile
from ui.renderers.plot_renderer import PlotRenderer
from ui.renderers.status_renderer import StatusRenderer
from ui.renderers.tile_renderer import TileRenderer


DEFAULT_EXECUTABLE_PATH = (
    r"C:\Users\Alfonso.Fernandez\CLionProjects\flight-computer-sim\flight-software"
    r"\cmake-build-debug\flight_computer_sim.exe"
)
REPLAY_STEP_FRAMES = 1
MAX_POINTS = 300
MAX_EVENTS = 200


class GroundStationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.auto_follow = True

        self.executable_path = DEFAULT_EXECUTABLE_PATH

        self.live_mode = False
        self.replay_mode = False
        self.paused = False
        self.stopped = False

        self.telemetry_parser = TelemetryParser()
        self.log_parser = LogParser()

        self.buffer = TelemetryBuffer(max_points=MAX_POINTS)
        self.event_logger = EventLogger(max_events=MAX_EVENTS)
        self.csv_logger = CsvTelemetryLogger()
        self.live_session = LiveSession()
        self.replay_session = ReplaySession(step_frames=REPLAY_STEP_FRAMES)

        self.plot_renderer = PlotRenderer(self.mode_color)
        self.status_renderer = StatusRenderer(self.health_status_text)
        self.tile_renderer = TileRenderer(
            self.health_status_text,
            self.mode_color,
            self.health_color,
            self.execution_color
        )

        script_dir = Path(__file__).resolve().parent.parent
        self.earth_map_path = script_dir / "res" / "world-map.jpg"

        self.setWindowTitle("Flight Computer Ground Station")
        self.resize(1950, 1000)

        self._build_ui()
        self._apply_styles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(200)

    # ---------- helpers ----------

    @staticmethod
    def health_status_text(status: int) -> str:
        if status == 0:
            return "OK"
        if status == 1:
            return "WARNING"
        if status == 2:
            return "CRITICAL"
        return "UNKNOWN"

    @staticmethod
    def mode_color(mode: str) -> str:
        if mode == "NOMINAL":
            return "#33d17a"
        if mode == "DEGRADED":
            return "#ffb347"
        if mode == "SAFE":
            return "#ff5c5c"
        return "#7f8c9a"

    @staticmethod
    def health_color(status: int) -> str:
        if status == 0:
            return "#33d17a"
        if status == 1:
            return "#ffb347"
        if status == 2:
            return "#ff5c5c"
        return "#7f8c9a"

    @staticmethod
    def execution_color(text: str) -> str:
        if text == "RUNNING":
            return "#33d17a"
        if text == "PAUSED":
            return "#ffb347"
        if text == "STOPPED":
            return "#ff5c5c"
        return "#7f8c9a"

    def style_toolbar(self, toolbar):
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1a2430;
                border: 1px solid #2e3c4b;
                spacing: 6px;
                padding: 4px;
            }
            QToolButton {
                background-color: #1a2430;
                color: #e6eef7;
                border: 1px solid #314152;
                border-radius: 4px;
                padding: 4px 6px;
                margin: 1px;
            }
            QToolButton:hover {
                background-color: #253444;
            }
            QToolButton:pressed {
                background-color: #31485f;
            }
        """)
        toolbar.setMovable(False)

        for action in toolbar.actions():
            widget = toolbar.widgetForAction(action)
            if isinstance(widget, QToolButton):
                widget.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

    def record_event(self, text: str):
        self.event_logger.record(text)

    def reset_buffers(self):
        self.buffer.reset()
        self.event_logger.clear()

    # ---------- UI ----------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self._build_controls(root)
        self._build_tiles(root)
        self._build_main_grid(root)
        self._build_footer(root)

    def _build_controls(self, root_layout):
        controls = QHBoxLayout()

        self.btn_select_exe = QPushButton("Select EXE")
        self.btn_start_live = QPushButton("Start Live")
        self.btn_open_replay = QPushButton("Open Replay")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_restart = QPushButton("Restart Replay")
        self.btn_stop = QPushButton("Stop")
        self.btn_auto_follow = QPushButton("Auto Follow: ON")
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

        for widget in [
            self.btn_select_exe, self.btn_start_live, self.btn_open_replay,
            self.btn_pause, self.btn_resume, self.btn_restart, self.btn_stop,
            self.btn_auto_follow, self.btn_screenshot,
            self.btn_reset_warn, self.btn_reset_all,
            self.btn_force_nom, self.btn_force_safe, self.btn_status, self.btn_help
        ]:
            controls.addWidget(widget)

        controls.addWidget(self.command_input, 1)
        controls.addWidget(self.btn_send)

        root_layout.addLayout(controls)

        self._connect_controls()

    def _build_tiles(self, root_layout):
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

        root_layout.addLayout(tiles_layout)

    def _build_main_grid(self, root_layout):
        grid = QGridLayout()
        grid.setSpacing(10)
        root_layout.addLayout(grid, 1)

        self.alt_plot = PlotWidget()
        self.accel_plot = PlotWidget()
        self.xy_plot = PlotWidget()
        self.hk_plot = PlotWidget()
        self.map_plot = PlotWidget()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)

        self.events_text = QTextEdit()
        self.events_text.setReadOnly(True)

        grid.addWidget(self._wrap_group("Altitude / Truth vs Measured", self.alt_plot), 0, 0)
        grid.addWidget(self._wrap_group("Accel Z / Truth vs Measured", self.accel_plot), 0, 1)
        grid.addWidget(self._wrap_group("Ground Track", self.map_plot), 0, 2)
        grid.addWidget(self._wrap_group("Accel X / Y + Gyro Z", self.xy_plot), 1, 0)
        grid.addWidget(self._wrap_group("Battery / Temperature", self.hk_plot), 1, 1)
        grid.addWidget(self._wrap_group("System Status", self.status_text), 1, 2)
        grid.addWidget(self._wrap_group("Event Log", self.events_text), 0, 3, 2, 1)

    def _build_footer(self, root_layout):
        self.footer_label = QLabel("Source: n/a | Session: IDLE | Current mode: UNKNOWN")
        root_layout.addWidget(self.footer_label)

    def _connect_controls(self):
        self.btn_select_exe.clicked.connect(self.select_executable)
        self.btn_start_live.clicked.connect(self.start_live)
        self.btn_open_replay.clicked.connect(self.open_replay_file)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_resume.clicked.connect(self.resume)
        self.btn_restart.clicked.connect(self.restart_replay)
        self.btn_stop.clicked.connect(self.stop_execution)
        self.btn_auto_follow.clicked.connect(self.toggle_auto_follow)
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

        if isinstance(widget, PlotWidget):
            toolbar = NavigationToolbar(widget, self)
            self.style_toolbar(toolbar)
            layout.addWidget(toolbar)

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

    # ---------- session control ----------

    def toggle_auto_follow(self):
        self.auto_follow = not self.auto_follow
        self.btn_auto_follow.setText(f"Auto Follow: {'ON' if self.auto_follow else 'OFF'}")
        self.record_event(f"OPERATOR  | auto_follow set to {self.auto_follow}")

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
        self._stop_all_sessions()
        self.reset_buffers()

        self.live_mode = True
        self.replay_mode = False
        self.paused = False
        self.stopped = False

        try:
            self.live_session.start(self.executable_path)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to start executable:\n{e}")
            self.live_mode = False
            return

        self.csv_logger.start()
        self.event_logger.start("live")
        self.record_event(f"LIVE      | simulator started: {self.executable_path}")

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

        self._stop_all_sessions()
        self.reset_buffers()

        self.live_mode = False
        self.replay_mode = True
        self.paused = False
        self.stopped = False

        try:
            self.replay_session.load(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Replay Error", f"Failed to load replay:\n{e}")
            self.replay_mode = False
            return

        self.event_logger.start("replay")
        self.record_event(f"REPLAY    | loaded file: {file_path}")

    def restart_replay(self):
        if not self.replay_mode:
            self.record_event("OPERATOR  | restart ignored (not in replay mode)")
            return

        self.replay_session.restart()
        self.paused = False
        self.stopped = False
        self.reset_buffers()
        self.record_event("REPLAY    | restarted")

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
        self._stop_all_sessions()

    def _stop_all_sessions(self):
        self.live_session.stop()
        self.csv_logger.stop()
        self.event_logger.stop()

    def save_screenshot(self):
        out_dir = Path("logs")
        out_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"screenshot_{timestamp}.png"

        self.grab().save(str(out_path))
        self.record_event(f"OPERATOR  | screenshot saved: {out_path}")

    # ---------- commands ----------

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

        try:
            self.live_session.send_command(cmd)
            self.record_event(f"OPERATOR  | sent command: {cmd}")
        except BrokenPipeError:
            self.record_event("OPERATOR  | failed to send command: stdin closed")
        except Exception as e:
            self.record_event(f"OPERATOR  | failed to send command: {e}")

    def send_manual_command(self):
        cmd = self.command_input.text().strip()
        if cmd:
            self.send_command(cmd)
            self.command_input.clear()

    # ---------- telemetry flow ----------

    def push_telemetry_frame(self, telemetry):
        mode_changed = self.buffer.append(telemetry)
        if mode_changed:
            transition_time_s = telemetry.time_ms / 1000.0
            self.record_event(f"T+{transition_time_s:6.1f}s | MODE -> {telemetry.mode}")

    def consume_live_output(self):
        if self.stopped or self.paused:
            return

        for line in self.live_session.consume_available_lines():
            if line == self.live_session.PROCESS_ENDED_MARKER:
                self.record_event("LIVE      | simulator process ended")
                self.live_mode = False
                self.live_session.stop()
                self.csv_logger.stop()
                return

            log_data = self.log_parser.parse(line)
            if log_data is not None:
                event_text = (
                    f"T+{log_data['time_ms'] / 1000.0:6.1f}s | "
                    f"{log_data['level']:5s} | {log_data['message']}"
                )
                self.record_event(event_text)

            telemetry = self.telemetry_parser.from_json_line(line)
            if telemetry is None:
                continue

            self.push_telemetry_frame(telemetry)
            self.csv_logger.log_frame(telemetry)

    def consume_replay_frames(self):
        if self.stopped or self.paused:
            return

        for telemetry in self.replay_session.next_frames():
            self.push_telemetry_frame(telemetry)

    # ---------- rendering ----------

    def render_tiles(self):
        self.tile_renderer.render(
            latest_frame=self.buffer.latest_frame,
            stopped=self.stopped,
            paused=self.paused,
            tile_mode=self.tile_mode,
            tile_phase=self.tile_phase,
            tile_health=self.tile_health,
            tile_execution=self.tile_execution,
            tile_gps=self.tile_gps,
            tile_battery=self.tile_battery,
            tile_temp=self.tile_temp
        )

    def render_plots(self):
        self.plot_renderer.render_altitude_plot(self.alt_plot, self.buffer, self.auto_follow)
        self.plot_renderer.render_accel_plot(self.accel_plot, self.buffer, self.auto_follow)
        self.plot_renderer.render_xy_plot(self.xy_plot, self.buffer, self.auto_follow)
        self.plot_renderer.render_hk_plot(self.hk_plot, self.buffer, self.auto_follow)

    def render_ground_track(self):
        self.plot_renderer.render_ground_track(
            plot_widget=self.map_plot,
            buffer_data=self.buffer,
            latest_frame=self.buffer.latest_frame,
            auto_follow=self.auto_follow,
            earth_map_path=self.earth_map_path
        )

    def render_status(self):
        replay_label = self.replay_session.progress_label() if self.replay_mode else "LIVE"
        new_text = self.status_renderer.build_status_text(
            latest_frame=self.buffer.latest_frame,
            stopped=self.stopped,
            paused=self.paused,
            replay_mode=self.replay_mode,
            replay_label=replay_label,
            event_log_path=self.event_logger.path
        )
        self.status_renderer.apply_text_preserving_scroll(self.status_text, new_text)

    def render_events(self):
        self.status_renderer.apply_text_preserving_scroll(
            self.events_text,
            self.event_logger.render_text()
        )

    def render_footer(self):
        source = (
            self.replay_session.csv_path
            if self.replay_mode
            else (self.csv_logger.csv_path.name if self.csv_logger.csv_path else "n/a")
        )
        session = "REPLAY" if self.replay_mode else ("LIVE" if self.live_mode else "IDLE")

        self.footer_label.setText(
            f"Source: {source} | Session: {session} | "
            f"Current mode: {self.buffer.latest_mode} | "
            f"Auto Follow: {'ON' if self.auto_follow else 'OFF'}"
        )

    def update_dashboard(self):
        if self.replay_mode:
            self.consume_replay_frames()
        elif self.live_mode:
            self.consume_live_output()

        self.render_tiles()
        self.render_plots()
        self.render_ground_track()
        self.render_status()
        self.render_events()
        self.render_footer()

    # ---------- lifecycle ----------

    def closeEvent(self, event):
        self._stop_all_sessions()
        event.accept()