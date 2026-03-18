#include "app/state_machine.h"
#include "common/types.h"
#include "test_utils.h"

void test_state_machine_init_sets_init_mode(void) {
    state_machine_init();
    TEST_ASSERT_EQUAL_INT(MODE_INIT, state_machine_get_mode());
}

void test_state_machine_set_mode_changes_mode(void) {
    state_machine_init();

    state_machine_set_mode(MODE_NOMINAL);
    TEST_ASSERT_EQUAL_INT(MODE_NOMINAL, state_machine_get_mode());

    state_machine_set_mode(MODE_DEGRADED);
    TEST_ASSERT_EQUAL_INT(MODE_DEGRADED, state_machine_get_mode());

    state_machine_set_mode(MODE_SAFE);
    TEST_ASSERT_EQUAL_INT(MODE_SAFE, state_machine_get_mode());
}