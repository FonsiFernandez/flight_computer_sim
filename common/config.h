#ifndef CONFIG_H
#define CONFIG_H

#define MAIN_LOOP_PERIOD_MS                500
#define DEGRADED_LOOP_PERIOD_MS            750
#define SAFE_MODE_LOOP_PERIOD_MS           1000

#define IMU_FAILURE_START_SAMPLE           40
#define IMU_FAILURE_END_SAMPLE             46

#define ALTIMETER_FAILURE_START_SAMPLE     20
#define ALTIMETER_FAILURE_END_SAMPLE       26

#define IMU_CRITICAL_THRESHOLD             3
#define IMU_RECOVERY_THRESHOLD             3

#define ALT_WARNING_THRESHOLD              3
#define ALT_RECOVERY_THRESHOLD             3

#endif