cmake_minimum_required(VERSION 3.16)
project(flight_computer_sim C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_executable(flight_computer_sim
        main.c
        bsp/time_port.c
        bsp/uart_port.c
        drivers/imu_sim.c
        drivers/altimeter_sim.c
        drivers/gps_sim.c
        drivers/hk_sim.c
        app/state_machine.c
        services/health_monitor.c
        services/logger.c
        services/telemetry.c
        services/fault_manager.c
        comms/command.c
        simulation/vehicle_model.c
        simulation/geo.c
)

target_include_directories(flight_computer_sim PRIVATE
        .
        common
        bsp
        drivers
        app
        services
        comms
)

target_link_libraries(flight_computer_sim m)

enable_testing()

add_executable(flight_computer_tests
        tests/test_main.c
        tests/test_state_machine.c
        tests/test_health_monitor.c
        tests/test_fault_manager.c
        tests/test_command.c
        tests/logger_stub.c
        app/state_machine.c
        services/health_monitor.c
        services/fault_manager.c
        comms/command.c
        simulation/vehicle_model.c
)

target_include_directories(flight_computer_tests PRIVATE
        .
)

add_test(NAME flight_computer_tests COMMAND flight_computer_tests)