import csv
import json
from pathlib import Path

from models.telemetry import TelemetryFrame


class TelemetryParser:
    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _safe_int(value, default=0) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return int(default)

    @staticmethod
    def _safe_str(value, default="") -> str:
        if value is None:
            return default
        return str(value)

    @classmethod
    def from_json_line(cls, line: str) -> TelemetryFrame | None:
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
            time_ms=cls._safe_int(data.get("time_ms", 0)),
            mode=cls._safe_str(data.get("mode", "UNKNOWN")),
            mission_phase=cls._safe_str(data.get("mission_phase", "UNKNOWN")),

            truth_time_s=cls._safe_float(truth.get("time_s", 0.0)),
            truth_lat_deg=cls._safe_float(truth.get("lat_deg", 0.0)),
            truth_lon_deg=cls._safe_float(truth.get("lon_deg", 0.0)),
            truth_altitude_m=cls._safe_float(truth.get("altitude_m", 0.0)),
            truth_velocity_z_mps=cls._safe_float(truth.get("velocity_z_mps", 0.0)),
            truth_acceleration_z_mps2=cls._safe_float(truth.get("acceleration_z_mps2", 0.0)),
            truth_pitch_deg=cls._safe_float(truth.get("pitch_deg", 0.0)),
            truth_pitch_rate_dps=cls._safe_float(truth.get("pitch_rate_dps", 0.0)),
            truth_ecef_x_m=cls._safe_float(truth.get("ecef_x_m", 0.0)),
            truth_ecef_y_m=cls._safe_float(truth.get("ecef_y_m", 0.0)),
            truth_ecef_z_m=cls._safe_float(truth.get("ecef_z_m", 0.0)),

            ax=cls._safe_float(imu.get("x", 0.0)),
            ay=cls._safe_float(imu.get("y", 0.0)),
            az=cls._safe_float(imu.get("z", 0.0)),
            gyro_z_dps=cls._safe_float(imu.get("gyro_z_dps", 0.0)),
            imu_valid=cls._safe_int(imu.get("valid", 0)),

            altitude_m=cls._safe_float(altimeter.get("altitude_m", 0.0)),
            alt_valid=cls._safe_int(altimeter.get("valid", 0)),

            gps_lat_deg=cls._safe_float(gps.get("lat_deg", 0.0)),
            gps_lon_deg=cls._safe_float(gps.get("lon_deg", 0.0)),
            gps_altitude_m=cls._safe_float(gps.get("altitude_m", 0.0)),
            gps_velocity_north_mps=cls._safe_float(gps.get("velocity_north_mps", 0.0)),
            gps_velocity_east_mps=cls._safe_float(gps.get("velocity_east_mps", 0.0)),
            gps_fix_valid=cls._safe_int(gps.get("fix_valid", 0)),

            battery_voltage_v=cls._safe_float(hk.get("battery_voltage_v", 0.0)),
            board_temp_c=cls._safe_float(hk.get("board_temp_c", 0.0)),
            hk_valid=cls._safe_int(hk.get("valid", 0)),

            imu_fault_count=cls._safe_int(health.get("imu_fault_count", 0)),
            imu_recovery_count=cls._safe_int(health.get("imu_recovery_count", 0)),
            alt_fault_count=cls._safe_int(health.get("alt_fault_count", 0)),
            alt_recovery_count=cls._safe_int(health.get("alt_recovery_count", 0)),
            imu_latched=cls._safe_int(health.get("imu_latched", 0)),
            alt_latched=cls._safe_int(health.get("alt_latched", 0)),
            health_status=cls._safe_int(health.get("status", 0)),
        )

    @classmethod
    def from_csv_row(cls, row: dict) -> TelemetryFrame:
        return TelemetryFrame(
            time_ms=cls._safe_int(row.get("time_ms")),
            mode=cls._safe_str(row.get("mode"), "UNKNOWN"),
            mission_phase=cls._safe_str(row.get("mission_phase"), "UNKNOWN"),

            truth_time_s=cls._safe_float(row.get("truth_time_s")),
            truth_lat_deg=cls._safe_float(row.get("truth_lat_deg")),
            truth_lon_deg=cls._safe_float(row.get("truth_lon_deg")),
            truth_altitude_m=cls._safe_float(row.get("truth_altitude_m")),
            truth_velocity_z_mps=cls._safe_float(row.get("truth_velocity_z_mps")),
            truth_acceleration_z_mps2=cls._safe_float(row.get("truth_acceleration_z_mps2")),
            truth_pitch_deg=cls._safe_float(row.get("truth_pitch_deg")),
            truth_pitch_rate_dps=cls._safe_float(row.get("truth_pitch_rate_dps")),
            truth_ecef_x_m=cls._safe_float(row.get("truth_ecef_x_m")),
            truth_ecef_y_m=cls._safe_float(row.get("truth_ecef_y_m")),
            truth_ecef_z_m=cls._safe_float(row.get("truth_ecef_z_m")),

            ax=cls._safe_float(row.get("ax")),
            ay=cls._safe_float(row.get("ay")),
            az=cls._safe_float(row.get("az")),
            gyro_z_dps=cls._safe_float(row.get("gyro_z_dps")),
            imu_valid=cls._safe_int(row.get("imu_valid")),

            altitude_m=cls._safe_float(row.get("altitude_m")),
            alt_valid=cls._safe_int(row.get("alt_valid")),

            gps_lat_deg=cls._safe_float(row.get("gps_lat_deg")),
            gps_lon_deg=cls._safe_float(row.get("gps_lon_deg")),
            gps_altitude_m=cls._safe_float(row.get("gps_altitude_m")),
            gps_velocity_north_mps=cls._safe_float(row.get("gps_velocity_north_mps")),
            gps_velocity_east_mps=cls._safe_float(row.get("gps_velocity_east_mps")),
            gps_fix_valid=cls._safe_int(row.get("gps_fix_valid")),

            battery_voltage_v=cls._safe_float(row.get("battery_voltage_v")),
            board_temp_c=cls._safe_float(row.get("board_temp_c")),
            hk_valid=cls._safe_int(row.get("hk_valid")),

            imu_fault_count=cls._safe_int(row.get("imu_fault_count")),
            imu_recovery_count=cls._safe_int(row.get("imu_recovery_count")),
            alt_fault_count=cls._safe_int(row.get("alt_fault_count")),
            alt_recovery_count=cls._safe_int(row.get("alt_recovery_count")),
            imu_latched=cls._safe_int(row.get("imu_latched")),
            alt_latched=cls._safe_int(row.get("alt_latched")),
            health_status=cls._safe_int(row.get("health_status")),
        )

    @classmethod
    def load_csv(cls, csv_path: str | Path) -> list[TelemetryFrame]:
        frames: list[TelemetryFrame] = []

        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                frames.append(cls.from_csv_row(row))

        return frames