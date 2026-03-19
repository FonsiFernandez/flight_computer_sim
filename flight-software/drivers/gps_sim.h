#ifndef GPS_SIM_H
#define GPS_SIM_H

#include "common/types.h"

void gps_sim_init(void);
gps_data_t gps_sim_read(void);

#endif