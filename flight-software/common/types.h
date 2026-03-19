#ifndef TYPES_H
#define TYPES_H

#include <stdbool.h>

typedef struct {
    float time_s;

    double lat_deg;
    double lon_deg;
    double alt_m;

    double ecef_x_m;
    double ecef_y_m;
    double ecef_z_m;

    double vel_north_mps;
    double vel_east_mps;
    double vel_down_mps;

    double acc_north_mps2;
    double acc_east_mps2;
    double acc_down_mps2;

    float pitch_deg;
    float pitch_rate_dps;

    float altitude_m;
    float velocity_z_mps;
    float acceleration_z_mps2;
} vehicle_truth_t;

typedef struct {
    float accel_x;
    float accel_y;
    float accel_z;
    float gyro_z_dps;
    bool valid;
} imu_data_t;

typedef struct {
    float altitude_m;
    bool valid;
} altimeter_data_t;

typedef struct {
    double lat_deg;
    double lon_deg;
    float altitude_m;
    float velocity_north_mps;
    float velocity_east_mps;
    bool fix_valid;
} gps_data_t;

typedef struct {
    float battery_voltage_v;
    float board_temp_c;
    bool valid;
} hk_data_t;

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

typedef struct {
    double lat_deg;
    double lon_deg;
    double alt_m;
} geodetic_position_t;

typedef struct {
    double x_m;
    double y_m;
    double z_m;
} ecef_position_t;

typedef struct {
    double north_mps;
    double east_mps;
    double down_mps;
} ned_velocity_t;

typedef struct {
    double north_mps2;
    double east_mps2;
    double down_mps2;
} ned_acceleration_t;

#endif