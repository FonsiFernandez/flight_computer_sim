#include <stdio.h>
#include <stdlib.h>

int tests_run = 0;
int tests_failed = 0;

void test_state_machine_init_sets_init_mode(void);
void test_state_machine_set_mode_changes_mode(void);

void test_health_monitor_init_starts_clean(void);
void test_health_monitor_warning_on_altimeter_fault(void);
void test_health_monitor_critical_on_imu_fault(void);
void test_health_monitor_altimeter_can_recover(void);
void test_health_monitor_imu_latch_stays_set(void);

void test_fault_manager_warning_moves_to_degraded(void);
void test_fault_manager_critical_moves_to_safe(void);
void test_fault_manager_ok_from_degraded_returns_nominal(void);
void test_fault_manager_manual_warning_reset_returns_nominal(void);
void test_fault_manager_manual_reset_all_clears_and_returns_nominal(void);

void test_command_parse_status(void);
void test_command_parse_reset_warnings(void);
void test_command_parse_reset_all(void);
void test_command_parse_force_nominal(void);
void test_command_parse_force_safe(void);
void test_command_parse_help(void);
void test_command_parse_quit(void);
void test_command_parse_empty_string(void);
void test_command_parse_unknown_command(void);
void test_command_parse_null_is_invalid(void);

#define RUN_TEST(fn) do { \
tests_run++; \
printf("[TEST] %s\n", #fn); \
fn(); \
} while(0)

int main(void) {
    RUN_TEST(test_state_machine_init_sets_init_mode);
    RUN_TEST(test_state_machine_set_mode_changes_mode);

    RUN_TEST(test_health_monitor_init_starts_clean);
    RUN_TEST(test_health_monitor_warning_on_altimeter_fault);
    RUN_TEST(test_health_monitor_critical_on_imu_fault);
    RUN_TEST(test_health_monitor_altimeter_can_recover);
    RUN_TEST(test_health_monitor_imu_latch_stays_set);

    RUN_TEST(test_fault_manager_warning_moves_to_degraded);
    RUN_TEST(test_fault_manager_critical_moves_to_safe);
    RUN_TEST(test_fault_manager_ok_from_degraded_returns_nominal);
    RUN_TEST(test_fault_manager_manual_warning_reset_returns_nominal);
    RUN_TEST(test_fault_manager_manual_reset_all_clears_and_returns_nominal);

    RUN_TEST(test_command_parse_status);
    RUN_TEST(test_command_parse_reset_warnings);
    RUN_TEST(test_command_parse_reset_all);
    RUN_TEST(test_command_parse_force_nominal);
    RUN_TEST(test_command_parse_force_safe);
    RUN_TEST(test_command_parse_help);
    RUN_TEST(test_command_parse_quit);
    RUN_TEST(test_command_parse_empty_string);
    RUN_TEST(test_command_parse_unknown_command);
    RUN_TEST(test_command_parse_null_is_invalid);

    printf("\nTests run: %d\n", tests_run);
    printf("Tests failed: %d\n", tests_failed);

    return tests_failed == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}