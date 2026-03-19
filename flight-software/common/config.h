#ifndef CONFIG_H
#define CONFIG_H

#define MAIN_LOOP_PERIOD_MS                500
#define DEGRADED_LOOP_PERIOD_MS            750
#define SAFE_MODE_LOOP_PERIOD_MS           1000

#define IMU_FAILURE_START_SAMPLE           40
#define IMU_FAILURE_END_SAMPLE             46

#define ALTIMETER_FAILURE_START_SAMPLE     20
#define ALTIMETER_FAILURE_END_SAMPLE       26

#define GPS_FAILURE_START_SAMPLE           55
#define GPS_FAILURE_END_SAMPLE             64

#define HK_FAILURE_START_SAMPLE            80
#define HK_FAILURE_END_SAMPLE              86

#define IMU_CRITICAL_THRESHOLD             3
#define IMU_RECOVERY_THRESHOLD             3

#define ALT_WARNING_THRESHOLD              3
#define ALT_RECOVERY_THRESHOLD             3

#define VEHICLE_DT_S                       0.5f

#define IMU_BIAS_X                         0.02f
#define IMU_BIAS_Y                        -0.01f
#define IMU_BIAS_Z                         0.05f
#define IMU_GYRO_Z_BIAS_DPS                0.15f

#define IMU_NOISE_X                        0.03f
#define IMU_NOISE_Y                        0.03f
#define IMU_NOISE_Z                        0.05f
#define IMU_GYRO_Z_NOISE_DPS               0.20f

#define ALTIMETER_BIAS_M                   1.20f
#define ALTIMETER_NOISE_M                  0.60f

#define GPS_ALTITUDE_BIAS_M                2.50f
#define GPS_ALTITUDE_NOISE_M               1.50f
#define GPS_VELOCITY_BIAS_MPS              0.30f
#define GPS_VELOCITY_NOISE_MPS             0.60f

#define HK_BATTERY_START_V                 16.8f
#define HK_BATTERY_DECAY_PER_STEP_V        0.015f
#define HK_TEMP_START_C                    25.0f
#define HK_TEMP_RISE_PER_STEP_C            0.08f
#define HK_TEMP_NOISE_C                    0.25f

#endif