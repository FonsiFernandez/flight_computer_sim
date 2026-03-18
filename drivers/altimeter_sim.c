#include "altimeter_sim.h"
#include "config.h"

static float altitude = 0.0f;
static int sample_count = 0;

void altimeter_sim_init(void) {
    altitude = 0.0f;
    sample_count = 0;
}

altimeter_data_t altimeter_sim_read(void) {
    altimeter_data_t data;
    sample_count++;

    altitude += 1.25f;

    data.altitude_m = altitude;
    data.valid = true;

    if (sample_count >= ALTIMETER_FAILURE_START_SAMPLE &&
        sample_count <= ALTIMETER_FAILURE_END_SAMPLE) {
        data.valid = false;
        }

    return data;
}