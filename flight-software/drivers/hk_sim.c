#include "drivers/hk_sim.h"
#include "common/config.h"

#include <stdlib.h>

static int sample_count = 0;
static float battery_voltage_v = HK_BATTERY_START_V;
static float board_temp_c = HK_TEMP_START_C;

static float random_symmetric(float amplitude) {
    float r = (float)rand() / (float)RAND_MAX;
    return (2.0f * r - 1.0f) * amplitude;
}

void hk_sim_init(void) {
    sample_count = 0;
    battery_voltage_v = HK_BATTERY_START_V;
    board_temp_c = HK_TEMP_START_C;
}

hk_data_t hk_sim_read(void) {
    hk_data_t data;

    sample_count++;

    battery_voltage_v -= HK_BATTERY_DECAY_PER_STEP_V;
    board_temp_c += HK_TEMP_RISE_PER_STEP_C;

    data.battery_voltage_v = battery_voltage_v;
    data.board_temp_c = board_temp_c + random_symmetric(HK_TEMP_NOISE_C);
    data.valid = true;

    if (sample_count >= HK_FAILURE_START_SAMPLE &&
        sample_count <= HK_FAILURE_END_SAMPLE) {
        data.valid = false;
        }

    return data;
}