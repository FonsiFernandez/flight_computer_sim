cmake_minimum_required(VERSION 3.16)
project(flight_computer_sim C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(
        .
        bsp
        drivers
        common
        app
        services
        comms
)

add_executable(flight_computer_sim
        main.c
        bsp/time_port.c
        bsp/uart_port.c
        drivers/imu_sim.c
        drivers/altimeter_sim.c
        app/state_machine.c
        services/health_monitor.c
        services/logger.c
        services/telemetry.c
        services/fault_manager.c
        comms/command.c
)

target_link_libraries(flight_computer_sim m)