#include "imu_sim.h"
#include "common/config.h"
#include <math.h>

static float t = 0.0f;
static int sample_count = 0;

void imu_sim_init(void) {
    t = 0.0f;
    sample_count = 0;
}

imu_data_t imu_sim_read(void) {
    imu_data_t data;
    sample_count++;

    data.accel_x = sinf(t) * 0.2f;
    data.accel_y = cosf(t) * 0.2f;
    data.accel_z = 9.81f;
    data.valid = true;

    t += 0.1f;

    if (sample_count >= IMU_FAILURE_START_SAMPLE &&
        sample_count <= IMU_FAILURE_END_SAMPLE) {
        data.valid = false;
        }

    return data;
}