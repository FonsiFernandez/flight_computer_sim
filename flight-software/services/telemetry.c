#include "services/telemetry.h"
#include "services/health_monitor.h"
#include "bsp/uart_port.h"

#include <stdio.h>

void telemetry_send(uint64_t elapsed_ms,
                    system_mode_t mode,
                    imu_data_t imu,
                    altimeter_data_t alt,
                    gps_data_t gps,
                    hk_data_t hk,
                    const vehicle_truth_t* truth,
                    const char* mission_phase) {
    char buffer[2200];
    const health_monitor_data_t* hm = health_monitor_get_data();

    const char* mode_str = "UNKNOWN";
    switch (mode) {
        case MODE_INIT: mode_str = "INIT"; break;
        case MODE_NOMINAL: mode_str = "NOMINAL"; break;
        case MODE_DEGRADED: mode_str = "DEGRADED"; break;
        case MODE_SAFE: mode_str = "SAFE"; break;
        default: break;
    }

    snprintf(buffer, sizeof(buffer),
             "{"
             "\"type\":\"telemetry\","
             "\"time_ms\":%llu,"
             "\"mode\":\"%s\","
             "\"mission_phase\":\"%s\","
             "\"truth\":{"
                 "\"time_s\":%.2f,"
                 "\"altitude_m\":%.2f,"
                 "\"velocity_z_mps\":%.2f,"
                 "\"acceleration_z_mps2\":%.2f,"
                 "\"pitch_deg\":%.2f,"
                 "\"pitch_rate_dps\":%.2f"
             "},"
             "\"imu\":{"
                 "\"x\":%.2f,"
                 "\"y\":%.2f,"
                 "\"z\":%.2f,"
                 "\"gyro_z_dps\":%.2f,"
                 "\"valid\":%d"
             "},"
             "\"altimeter\":{"
                 "\"altitude_m\":%.2f,"
                 "\"valid\":%d"
             "},"
             "\"gps\":{"
                 "\"altitude_m\":%.2f,"
                 "\"velocity_z_mps\":%.2f,"
                 "\"fix_valid\":%d"
             "},"
             "\"hk\":{"
                 "\"battery_voltage_v\":%.2f,"
                 "\"board_temp_c\":%.2f,"
                 "\"valid\":%d"
             "},"
             "\"health\":{"
                 "\"imu_fault_count\":%d,"
                 "\"imu_recovery_count\":%d,"
                 "\"alt_fault_count\":%d,"
                 "\"alt_recovery_count\":%d,"
                 "\"imu_latched\":%d,"
                 "\"alt_latched\":%d,"
                 "\"status\":%d"
             "}"
             "}",
             (unsigned long long)elapsed_ms,
             mode_str,
             mission_phase,
             truth->time_s,
             truth->altitude_m,
             truth->velocity_z_mps,
             truth->acceleration_z_mps2,
             truth->pitch_deg,
             truth->pitch_rate_dps,
             imu.accel_x,
             imu.accel_y,
             imu.accel_z,
             imu.gyro_z_dps,
             imu.valid,
             alt.altitude_m,
             alt.valid,
             gps.altitude_m,
             gps.velocity_z_mps,
             gps.fix_valid,
             hk.battery_voltage_v,
             hk.board_temp_c,
             hk.valid,
             hm->imu_fault_count,
             hm->imu_recovery_count,
             hm->alt_fault_count,
             hm->alt_recovery_count,
             hm->imu_fault_latched,
             hm->alt_fault_latched,
             hm->current_status);

    uart_send_line(buffer);
}