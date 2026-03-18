#ifndef TYPES_H
#define TYPES_H

#include <stdbool.h>

typedef struct {
    float accel_x;
    float accel_y;
    float accel_z;
    bool valid;
} imu_data_t;

typedef struct {
    float altitude_m;
    bool valid;
} altimeter_data_t;

typedef enum {
    MODE_INIT = 0,
    MODE_NOMINAL,
    MODE_DEGRADED,
    MODE_SAFE
} system_mode_t;

typedef enum {
    HEALTH_OK = 0,
    HEALTH_WARNING,
    HEALTH_CRITICAL
} health_status_t;

typedef struct {
    int imu_fault_count;
    int imu_recovery_count;
    int alt_fault_count;
    int alt_recovery_count;

    bool imu_fault_latched;
    bool alt_fault_latched;

    health_status_t current_status;
} health_monitor_data_t;

typedef enum {
    COMMAND_NONE = 0,
    COMMAND_STATUS,
    COMMAND_RESET_WARNINGS,
    COMMAND_RESET_ALL,
    COMMAND_FORCE_NOMINAL,
    COMMAND_FORCE_SAFE,
    COMMAND_HELP,
    COMMAND_QUIT
} command_type_t;

typedef struct {
    command_type_t type;
    bool valid;
} command_t;

#endif