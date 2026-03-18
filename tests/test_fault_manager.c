#include "fault_manager.h"
#include "health_monitor.h"
#include "state_machine.h"
#include "types.h"
#include "test_utils.h"

void test_fault_manager_warning_moves_to_degraded(void) {
    state_machine_init();
    health_monitor_init();
    fault_manager_init();

    state_machine_set_mode(MODE_NOMINAL);

    system_mode_t mode = fault_manager_update(HEALTH_WARNING, state_machine_get_mode());

    TEST_ASSERT_EQUAL_INT(MODE_DEGRADED, mode);
    TEST_ASSERT_EQUAL_INT(MODE_DEGRADED, state_machine_get_mode());
}

void test_fault_manager_critical_moves_to_safe(void) {
    state_machine_init();
    health_monitor_init();
    fault_manager_init();

    state_machine_set_mode(MODE_NOMINAL);

    system_mode_t mode = fault_manager_update(HEALTH_CRITICAL, state_machine_get_mode());

    TEST_ASSERT_EQUAL_INT(MODE_SAFE, mode);
    TEST_ASSERT_EQUAL_INT(MODE_SAFE, state_machine_get_mode());
}

void test_fault_manager_ok_from_degraded_returns_nominal(void) {
    state_machine_init();
    health_monitor_init();
    fault_manager_init();

    state_machine_set_mode(MODE_DEGRADED);

    system_mode_t mode = fault_manager_update(HEALTH_OK, state_machine_get_mode());

    TEST_ASSERT_EQUAL_INT(MODE_NOMINAL, mode);
    TEST_ASSERT_EQUAL_INT(MODE_NOMINAL, state_machine_get_mode());
}

void test_fault_manager_manual_warning_reset_returns_nominal(void) {
    state_machine_init();
    health_monitor_init();
    fault_manager_init();

    state_machine_set_mode(MODE_DEGRADED);
    fault_manager_process_manual_reset_warnings();

    TEST_ASSERT_EQUAL_INT(MODE_NOMINAL, state_machine_get_mode());
}

void test_fault_manager_manual_reset_all_clears_and_returns_nominal(void) {
    state_machine_init();
    health_monitor_init();
    fault_manager_init();

    state_machine_set_mode(MODE_SAFE);
    fault_manager_process_manual_reset_all();

    TEST_ASSERT_EQUAL_INT(MODE_NOMINAL, state_machine_get_mode());

    const health_monitor_data_t *hm = health_monitor_get_data();
    TEST_ASSERT_FALSE(hm->imu_fault_latched);
    TEST_ASSERT_FALSE(hm->alt_fault_latched);
    TEST_ASSERT_EQUAL_INT(HEALTH_OK, hm->current_status);
}