import csv
from datetime import datetime
from pathlib import Path

from models.telemetry import TelemetryFrame


class CsvTelemetryLogger:
    HEADER = [
        "time_ms",
        "mode",
        "mission_phase",
        "truth_time_s",
        "truth_lat_deg",
        "truth_lon_deg",
        "truth_altitude_m",
        "truth_velocity_z_mps",
        "truth_acceleration_z_mps2",
        "truth_pitch_deg",
        "truth_pitch_rate_dps",
        "truth_ecef_x_m",
        "truth_ecef_y_m",
        "truth_ecef_z_m",
        "ax",
        "ay",
        "az",
        "gyro_z_dps",
        "imu_valid",
        "altitude_m",
        "alt_valid",
        "gps_lat_deg",
        "gps_lon_deg",
        "gps_altitude_m",
        "gps_velocity_north_mps",
        "gps_velocity_east_mps",
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
    ]

    def __init__(self, logs_dir: str | Path = "logs"):
        self.logs_dir = Path(logs_dir)
        self.csv_file = None
        self.csv_writer = None
        self.csv_path: Path | None = None

    def start(self) -> Path:
        self.logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.logs_dir / f"telemetry_{timestamp}.csv"

        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(self.HEADER)
        self.csv_file.flush()

        return self.csv_path

    def log_frame(self, frame: TelemetryFrame) -> None:
        if self.csv_writer is None or self.csv_file is None:
            return

        self.csv_writer.writerow([
            frame.time_ms,
            frame.mode,
            frame.mission_phase,
            frame.truth_time_s,
            frame.truth_lat_deg,
            frame.truth_lon_deg,
            frame.truth_altitude_m,
            frame.truth_velocity_z_mps,
            frame.truth_acceleration_z_mps2,
            frame.truth_pitch_deg,
            frame.truth_pitch_rate_dps,
            frame.truth_ecef_x_m,
            frame.truth_ecef_y_m,
            frame.truth_ecef_z_m,
            frame.ax,
            frame.ay,
            frame.az,
            frame.gyro_z_dps,
            frame.imu_valid,
            frame.altitude_m,
            frame.alt_valid,
            frame.gps_lat_deg,
            frame.gps_lon_deg,
            frame.gps_altitude_m,
            frame.gps_velocity_north_mps,
            frame.gps_velocity_east_mps,
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

    def stop(self) -> None:
        if self.csv_file is not None:
            self.csv_file.close()

        self.csv_file = None
        self.csv_writer = None
        self.csv_path = None