#ifndef IMU_SIM_H
#define IMU_SIM_H

#include "common/types.h"

void imu_sim_init(void);
imu_data_t imu_sim_read(void);

#endif