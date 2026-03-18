#include "fault_manager.h"
#include "app/state_machine.h"
#include "health_monitor.h"
#include "logger.h"

void fault_manager_init(void) {
}

system_mode_t fault_manager_update(health_status_t health, system_mode_t current_mode) {
    if (health == HEALTH_CRITICAL && current_mode != MODE_SAFE) {
        logger_error("Critical fault detected. Switching to SAFE mode.");
        state_machine_set_mode(MODE_SAFE);
        return state_machine_get_mode();
    }

    if (health == HEALTH_WARNING && current_mode == MODE_NOMINAL) {
        logger_warn("Recoverable fault detected. Switching to DEGRADED mode.");
        state_machine_set_mode(MODE_DEGRADED);
        return state_machine_get_mode();
    }

    if (health == HEALTH_OK && current_mode == MODE_DEGRADED) {
        logger_info("Recovered from warning condition. Returning to NOMINAL mode.");
        state_machine_set_mode(MODE_NOMINAL);
        return state_machine_get_mode();
    }

    return current_mode;
}

void fault_manager_process_manual_reset_warnings(void) {
    health_monitor_reset_warning_latches();

    if (state_machine_get_mode() == MODE_DEGRADED) {
        state_machine_set_mode(MODE_NOMINAL);
        logger_info("Manual warning reset applied. Returning to NOMINAL mode.");
    } else {
        logger_info("Manual warning reset applied.");
    }
}

void fault_manager_process_manual_reset_all(void) {
    health_monitor_reset_all_latches();
    state_machine_set_mode(MODE_NOMINAL);
    logger_warn("Manual reset of all latches applied. Forcing NOMINAL mode.");
}

void fault_manager_force_mode(system_mode_t mode) {
    state_machine_set_mode(mode);

    switch (mode) {
        case MODE_NOMINAL:
            logger_warn("Operator forced NOMINAL mode.");
            break;
        case MODE_DEGRADED:
            logger_warn("Operator forced DEGRADED mode.");
            break;
        case MODE_SAFE:
            logger_warn("Operator forced SAFE mode.");
            break;
        default:
            break;
    }
}