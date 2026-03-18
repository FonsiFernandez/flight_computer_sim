#ifndef HEALTH_MONITOR_H
#define HEALTH_MONITOR_H

#include "types.h"

void health_monitor_init(void);
health_status_t health_monitor_update(imu_data_t imu, altimeter_data_t alt);
const health_monitor_data_t* health_monitor_get_data(void);

void health_monitor_reset_warning_latches(void);
void health_monitor_reset_all_latches(void);

#endif