#include "health_monitor.h"
#include "common/config.h"

static health_monitor_data_t hm;

void health_monitor_init(void) {
    hm.imu_fault_count = 0;
    hm.imu_recovery_count = 0;
    hm.alt_fault_count = 0;
    hm.alt_recovery_count = 0;

    hm.imu_fault_latched = false;
    hm.alt_fault_latched = false;

    hm.current_status = HEALTH_OK;
}

static void update_imu_counters(imu_data_t imu) {
    if (!imu.valid) {
        hm.imu_fault_count++;
        hm.imu_recovery_count = 0;
    } else {
        hm.imu_recovery_count++;
        hm.imu_fault_count = 0;
    }

    if (hm.imu_fault_count >= IMU_CRITICAL_THRESHOLD) {
        hm.imu_fault_latched = true;
    }
}

static void update_altimeter_counters(altimeter_data_t alt) {
    if (!alt.valid) {
        hm.alt_fault_count++;
        hm.alt_recovery_count = 0;
    } else {
        hm.alt_recovery_count++;
        hm.alt_fault_count = 0;
    }

    if (hm.alt_fault_count >= ALT_WARNING_THRESHOLD) {
        hm.alt_fault_latched = true;
    }

    if (hm.alt_fault_latched && hm.alt_recovery_count >= ALT_RECOVERY_THRESHOLD) {
        hm.alt_fault_latched = false;
    }
}

health_status_t health_monitor_update(imu_data_t imu, altimeter_data_t alt) {
    update_imu_counters(imu);
    update_altimeter_counters(alt);

    if (hm.imu_fault_latched) {
        hm.current_status = HEALTH_CRITICAL;
        return hm.current_status;
    }

    if (hm.alt_fault_latched) {
        hm.current_status = HEALTH_WARNING;
        return hm.current_status;
    }

    hm.current_status = HEALTH_OK;
    return hm.current_status;
}

const health_monitor_data_t* health_monitor_get_data(void) {
    return &hm;
}

void health_monitor_reset_warning_latches(void) {
    hm.alt_fault_latched = false;
    hm.alt_fault_count = 0;
    hm.alt_recovery_count = 0;

    if (hm.imu_fault_latched) {
        hm.current_status = HEALTH_CRITICAL;
    } else {
        hm.current_status = HEALTH_OK;
    }
}

void health_monitor_reset_all_latches(void) {
    hm.imu_fault_latched = false;
    hm.alt_fault_latched = false;

    hm.imu_fault_count = 0;
    hm.imu_recovery_count = 0;
    hm.alt_fault_count = 0;
    hm.alt_recovery_count = 0;

    hm.current_status = HEALTH_OK;
}