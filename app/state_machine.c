#include "state_machine.h"

static system_mode_t current_mode = MODE_INIT;

void state_machine_init(void) {
    current_mode = MODE_INIT;
}

system_mode_t state_machine_get_mode(void) {
    return current_mode;
}

void state_machine_set_mode(system_mode_t mode) {
    current_mode = mode;
}

const char* state_machine_get_mode_string(system_mode_t mode) {
    switch (mode) {
        case MODE_INIT:
            return "INIT";
        case MODE_NOMINAL:
            return "NOMINAL";
        case MODE_DEGRADED:
            return "DEGRADED";
        case MODE_SAFE:
            return "SAFE";
        default:
            return "UNKNOWN";
    }
}