#include "bsp/time_port.h"
#include "drivers/imu_sim.h"
#include "drivers/altimeter_sim.h"
#include "app/state_machine.h"
#include "common/config.h"
#include "services/health_monitor.h"
#include "services/logger.h"
#include "services/telemetry.h"
#include "services/fault_manager.h"
#include "comms/command.h"
#include "simulation/vehicle_model.h"

#include <stdint.h>
#include <stdio.h>

static void process_command(command_t cmd) {
    if (!cmd.valid) {
        logger_warn("Unknown command. Type 'help'.");
        return;
    }

    switch (cmd.type) {
        case COMMAND_NONE:
            break;

        case COMMAND_STATUS:
            logger_info("Status command received.");
            break;

        case COMMAND_RESET_WARNINGS:
            fault_manager_process_manual_reset_warnings();
            break;

        case COMMAND_RESET_ALL:
            fault_manager_process_manual_reset_all();
            break;

        case COMMAND_FORCE_NOMINAL:
            fault_manager_force_mode(MODE_NOMINAL);
            break;

        case COMMAND_FORCE_SAFE:
            fault_manager_force_mode(MODE_SAFE);
            break;

        case COMMAND_HELP:
            logger_info("Commands: status, reset_warnings, reset_all, force_nominal, force_safe, help, quit");
            break;

        case COMMAND_QUIT:
            logger_warn("Quit command received. Stopping simulation.");
            break;
    }
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    logger_init();
    logger_info("Flight Computer Sim START");

    imu_sim_init();
    altimeter_sim_init();
    state_machine_init();
    health_monitor_init();
    fault_manager_init();
    command_init();
    vehicle_model_init();

    state_machine_set_mode(MODE_NOMINAL);
    logger_info("System entered NOMINAL mode");

    uint64_t start = time_now_ms();
    system_mode_t last_mode = MODE_INIT;
    bool running = true;

    while (running) {
        vehicle_model_step(VEHICLE_DT_S);
        command_t cmd = command_poll();
        if (cmd.type == COMMAND_QUIT) {
            process_command(cmd);
            break;
        }
        process_command(cmd);

        uint64_t now = time_now_ms();
        uint64_t elapsed = now - start;

        imu_data_t imu = imu_sim_read();
        altimeter_data_t alt = altimeter_sim_read();

        health_status_t health = health_monitor_update(imu, alt);
        system_mode_t current_mode = state_machine_get_mode();
        current_mode = fault_manager_update(health, current_mode);

        if (current_mode != last_mode) {
            switch (current_mode) {
                case MODE_NOMINAL:
                    logger_info("Mode transition: NOMINAL");
                    break;
                case MODE_DEGRADED:
                    logger_warn("Mode transition: DEGRADED");
                    break;
                case MODE_SAFE:
                    logger_error("Mode transition: SAFE");
                    break;
                default:
                    break;
            }
            last_mode = current_mode;
        }

        const vehicle_truth_t* truth = vehicle_model_get_truth();
        const char* mission_phase = vehicle_model_get_phase();
        telemetry_send(elapsed, current_mode, imu, alt, truth, mission_phase);

        switch (current_mode) {
            case MODE_SAFE:
                time_sleep_ms(SAFE_MODE_LOOP_PERIOD_MS);
                break;
            case MODE_DEGRADED:
                time_sleep_ms(DEGRADED_LOOP_PERIOD_MS);
                break;
            case MODE_NOMINAL:
            default:
                time_sleep_ms(MAIN_LOOP_PERIOD_MS);
                break;
        }
    }

    logger_info("Flight Computer Sim STOP");
    return 0;
}