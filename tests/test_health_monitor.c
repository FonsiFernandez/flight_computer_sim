#include "health_monitor.h"
#include "config.h"
#include "types.h"
#include "test_utils.h"

static imu_data_t make_imu(bool valid) {
    imu_data_t imu;
    imu.accel_x = 0.0f;
    imu.accel_y = 0.0f;
    imu.accel_z = 9.81f;
    imu.valid = valid;
    return imu;
}

static altimeter_data_t make_alt(bool valid) {
    altimeter_data_t alt;
    alt.altitude_m = 100.0f;
    alt.valid = valid;
    return alt;
}

void test_health_monitor_init_starts_clean(void) {
    health_monitor_init();

    const health_monitor_data_t *hm = health_monitor_get_data();

    TEST_ASSERT_EQUAL_INT(0, hm->imu_fault_count);
    TEST_ASSERT_EQUAL_INT(0, hm->alt_fault_count);
    TEST_ASSERT_FALSE(hm->imu_fault_latched);
    TEST_ASSERT_FALSE(hm->alt_fault_latched);
    TEST_ASSERT_EQUAL_INT(HEALTH_OK, hm->current_status);
}

void test_health_monitor_warning_on_altimeter_fault(void) {
    health_monitor_init();

    imu_data_t imu = make_imu(true);
    altimeter_data_t alt = make_alt(false);

    health_status_t status = HEALTH_OK;
    for (int i = 0; i < ALT_WARNING_THRESHOLD; i++) {
        status = health_monitor_update(imu, alt);
    }

    TEST_ASSERT_EQUAL_INT(HEALTH_WARNING, status);

    const health_monitor_data_t *hm = health_monitor_get_data();
    TEST_ASSERT_TRUE(hm->alt_fault_latched);
}

void test_health_monitor_critical_on_imu_fault(void) {
    health_monitor_init();

    imu_data_t imu = make_imu(false);
    altimeter_data_t alt = make_alt(true);

    health_status_t status = HEALTH_OK;
    for (int i = 0; i < IMU_CRITICAL_THRESHOLD; i++) {
        status = health_monitor_update(imu, alt);
    }

    TEST_ASSERT_EQUAL_INT(HEALTH_CRITICAL, status);

    const health_monitor_data_t *hm = health_monitor_get_data();
    TEST_ASSERT_TRUE(hm->imu_fault_latched);
}

void test_health_monitor_altimeter_can_recover(void) {
    health_monitor_init();

    imu_data_t imu = make_imu(true);
    altimeter_data_t alt_bad = make_alt(false);
    altimeter_data_t alt_good = make_alt(true);

    for (int i = 0; i < ALT_WARNING_THRESHOLD; i++) {
        health_monitor_update(imu, alt_bad);
    }

    TEST_ASSERT_TRUE(health_monitor_get_data()->alt_fault_latched);

    health_status_t status = HEALTH_WARNING;
    for (int i = 0; i < ALT_RECOVERY_THRESHOLD; i++) {
        status = health_monitor_update(imu, alt_good);
    }

    TEST_ASSERT_EQUAL_INT(HEALTH_OK, status);
    TEST_ASSERT_FALSE(health_monitor_get_data()->alt_fault_latched);
}

void test_health_monitor_imu_latch_stays_set(void) {
    health_monitor_init();

    imu_data_t imu_bad = make_imu(false);
    imu_data_t imu_good = make_imu(true);
    altimeter_data_t alt = make_alt(true);

    for (int i = 0; i < IMU_CRITICAL_THRESHOLD; i++) {
        health_monitor_update(imu_bad, alt);
    }

    TEST_ASSERT_TRUE(health_monitor_get_data()->imu_fault_latched);

    health_status_t status = HEALTH_OK;
    for (int i = 0; i < IMU_RECOVERY_THRESHOLD + 2; i++) {
        status = health_monitor_update(imu_good, alt);
    }

    TEST_ASSERT_EQUAL_INT(HEALTH_CRITICAL, status);
    TEST_ASSERT_TRUE(health_monitor_get_data()->imu_fault_latched);
}