#ifndef TELEMETRY_H
#define TELEMETRY_H

#include "common/types.h"
#include <stdint.h>

void telemetry_send(uint64_t elapsed_ms, system_mode_t mode, imu_data_t imu, altimeter_data_t alt);

#endif