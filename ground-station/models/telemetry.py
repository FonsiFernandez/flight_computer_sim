from dataclasses import dataclass


@dataclass
class TelemetryFrame:
    time_ms: int
    mode: str
    mission_phase: str

    truth_time_s: float
    truth_lat_deg: float
    truth_lon_deg: float
    truth_altitude_m: float
    truth_velocity_z_mps: float
    truth_acceleration_z_mps2: float
    truth_pitch_deg: float
    truth_pitch_rate_dps: float
    truth_ecef_x_m: float
    truth_ecef_y_m: float
    truth_ecef_z_m: float

    ax: float
    ay: float
    az: float
    gyro_z_dps: float
    imu_valid: int

    altitude_m: float
    alt_valid: int

    gps_lat_deg: float
    gps_lon_deg: float
    gps_altitude_m: float
    gps_velocity_north_mps: float
    gps_velocity_east_mps: float
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