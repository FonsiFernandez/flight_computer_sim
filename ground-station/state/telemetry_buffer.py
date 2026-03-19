from collections import deque

from models.telemetry import TelemetryFrame


class TelemetryBuffer:
    def __init__(self, max_points: int = 300):
        self.max_points = max_points
        self.reset()

    def reset(self) -> None:
        self.times = deque(maxlen=self.max_points)

        self.altitudes = deque(maxlen=self.max_points)
        self.truth_altitudes = deque(maxlen=self.max_points)
        self.gps_altitudes = deque(maxlen=self.max_points)

        self.accel_x = deque(maxlen=self.max_points)
        self.accel_y = deque(maxlen=self.max_points)
        self.accel_z = deque(maxlen=self.max_points)
        self.truth_accel_z = deque(maxlen=self.max_points)
        self.gyro_z = deque(maxlen=self.max_points)

        self.battery_voltage = deque(maxlen=self.max_points)
        self.board_temp = deque(maxlen=self.max_points)

        self.truth_lat = deque(maxlen=self.max_points)
        self.truth_lon = deque(maxlen=self.max_points)
        self.gps_lat = deque(maxlen=self.max_points)
        self.gps_lon = deque(maxlen=self.max_points)

        self.altitude_error = deque(maxlen=self.max_points)
        self.accel_z_error = deque(maxlen=self.max_points)

        self.latest_frame: TelemetryFrame | None = None
        self.latest_mode = "UNKNOWN"

        self.mode_transitions: list[tuple[float, str]] = []
        self.last_transition_mode: str | None = None

    def append(self, telemetry: TelemetryFrame) -> bool:
        time_s = telemetry.time_ms / 1000.0

        self.times.append(time_s)

        self.altitudes.append(telemetry.altitude_m)
        self.truth_altitudes.append(telemetry.truth_altitude_m)
        self.gps_altitudes.append(telemetry.gps_altitude_m)

        self.accel_x.append(telemetry.ax)
        self.accel_y.append(telemetry.ay)
        self.accel_z.append(telemetry.az)
        self.truth_accel_z.append(telemetry.truth_acceleration_z_mps2)
        self.gyro_z.append(telemetry.gyro_z_dps)

        self.battery_voltage.append(telemetry.battery_voltage_v)
        self.board_temp.append(telemetry.board_temp_c)

        self.truth_lat.append(telemetry.truth_lat_deg)
        self.truth_lon.append(telemetry.truth_lon_deg)
        self.gps_lat.append(telemetry.gps_lat_deg)
        self.gps_lon.append(telemetry.gps_lon_deg)

        self.altitude_error.append(telemetry.altitude_m - telemetry.truth_altitude_m)
        self.accel_z_error.append(telemetry.az - telemetry.truth_acceleration_z_mps2)

        self.latest_frame = telemetry
        self.latest_mode = telemetry.mode

        return self._register_mode_transition_if_needed(telemetry)

    def _register_mode_transition_if_needed(self, telemetry: TelemetryFrame) -> bool:
        if telemetry.mode != self.last_transition_mode:
            transition_time_s = telemetry.time_ms / 1000.0
            self.mode_transitions.append((transition_time_s, telemetry.mode))
            self.last_transition_mode = telemetry.mode
            return True
        return False