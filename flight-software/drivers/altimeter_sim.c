#include "drivers/altimeter_sim.h"
#include "common/config.h"
#include "simulation/vehicle_model.h"

#include <stdlib.h>

static int sample_count = 0;

static float random_symmetric(float amplitude) {
    float r = (float)rand() / (float)RAND_MAX;
    return (2.0f * r - 1.0f) * amplitude;
}

void altimeter_sim_init(void) {
    sample_count = 0;
}

altimeter_data_t altimeter_sim_read(void) {
    altimeter_data_t data;
    const vehicle_truth_t* truth = vehicle_model_get_truth();

    sample_count++;

    data.altitude_m = truth->altitude_m + ALTIMETER_BIAS_M + random_symmetric(ALTIMETER_NOISE_M);
    data.valid = true;

    if (sample_count >= ALTIMETER_FAILURE_START_SAMPLE &&
        sample_count <= ALTIMETER_FAILURE_END_SAMPLE) {
        data.valid = false;
        }

    return data;
}