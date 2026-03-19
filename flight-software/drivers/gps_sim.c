#include "drivers/gps_sim.h"
#include "common/config.h"
#include "simulation/vehicle_model.h"

#include <stdlib.h>

static int sample_count = 0;

static float random_symmetric(float amplitude) {
    float r = (float)rand() / (float)RAND_MAX;
    return (2.0f * r - 1.0f) * amplitude;
}

void gps_sim_init(void) {
    sample_count = 0;
}

gps_data_t gps_sim_read(void) {
    gps_data_t data;
    const vehicle_truth_t* truth = vehicle_model_get_truth();

    sample_count++;

    data.altitude_m = truth->altitude_m + GPS_ALTITUDE_BIAS_M + random_symmetric(GPS_ALTITUDE_NOISE_M);
    data.velocity_z_mps = truth->velocity_z_mps + GPS_VELOCITY_BIAS_MPS + random_symmetric(GPS_VELOCITY_NOISE_MPS);
    data.fix_valid = true;

    if (sample_count >= GPS_FAILURE_START_SAMPLE &&
        sample_count <= GPS_FAILURE_END_SAMPLE) {
        data.fix_valid = false;
        }

    return data;
}