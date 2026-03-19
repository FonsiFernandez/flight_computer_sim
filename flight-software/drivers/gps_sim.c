#include "drivers/gps_sim.h"
#include "common/config.h"
#include "simulation/vehicle_model.h"

#include <stdlib.h>

static int sample_count = 0;

static double random_symmetric(double amplitude) {
    double r = (double)rand() / (double)RAND_MAX;
    return (2.0 * r - 1.0) * amplitude;
}

void gps_sim_init(void) {
    sample_count = 0;
}

gps_data_t gps_sim_read(void) {
    gps_data_t data;
    const vehicle_truth_t* truth = vehicle_model_get_truth();

    sample_count++;

    data.lat_deg = truth->lat_deg + random_symmetric(0.00001);
    data.lon_deg = truth->lon_deg + random_symmetric(0.00001);
    data.altitude_m = truth->altitude_m + (float)random_symmetric(1.5);
    data.velocity_north_mps = (float)(truth->vel_north_mps + random_symmetric(0.5));
    data.velocity_east_mps = (float)(truth->vel_east_mps + random_symmetric(0.5));
    data.fix_valid = true;

    if (sample_count >= GPS_FAILURE_START_SAMPLE &&
        sample_count <= GPS_FAILURE_END_SAMPLE) {
        data.fix_valid = false;
        }

    return data;
}