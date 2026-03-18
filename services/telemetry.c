#include "telemetry.h"
#include "state_machine.h"
#include "uart_port.h"
#include "health_monitor.h"

#include <stdio.h>

void telemetry_send(uint64_t elapsed_ms, system_mode_t mode, imu_data_t imu, altimeter_data_t alt) {
    char buffer[512];
    const health_monitor_data_t* hm = health_monitor_get_data();

    snprintf(buffer, sizeof(buffer),
             "TIME=%llu ms | MODE=%s | "
             "IMU[x=%.2f y=%.2f z=%.2f valid=%d] | "
             "ALT[%.2f m valid=%d] | "
             "HM[imu_fault=%d imu_rec=%d alt_fault=%d alt_rec=%d imu_lat=%d alt_lat=%d status=%d]",
             (unsigned long long)elapsed_ms,
             state_machine_get_mode_string(mode),
             imu.accel_x,
             imu.accel_y,
             imu.accel_z,
             imu.valid,
             alt.altitude_m,
             alt.valid,
             hm->imu_fault_count,
             hm->imu_recovery_count,
             hm->alt_fault_count,
             hm->alt_recovery_count,
             hm->imu_fault_latched,
             hm->alt_fault_latched,
             hm->current_status);

    uart_send_line(buffer);
}