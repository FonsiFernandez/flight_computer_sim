#include "drivers/imu_sim.h"
#include "common/config.h"
#include "simulation/vehicle_model.h"

#include <stdlib.h>

static int sample_count = 0;

static float random_symmetric(float amplitude) {
    float r = (float)rand() / (float)RAND_MAX;
    return (2.0f * r - 1.0f) * amplitude;
}

void imu_sim_init(void) {
    sample_count = 0;
}

imu_data_t imu_sim_read(void) {
    imu_data_t data;
    const vehicle_truth_t* truth = vehicle_model_get_truth();

    sample_count++;

    data.accel_x = IMU_BIAS_X + random_symmetric(IMU_NOISE_X);
    data.accel_y = IMU_BIAS_Y + random_symmetric(IMU_NOISE_Y);
    data.accel_z = truth->acceleration_z_mps2 + IMU_BIAS_Z + random_symmetric(IMU_NOISE_Z);
    data.valid = true;

    if (sample_count >= IMU_FAILURE_START_SAMPLE &&
        sample_count <= IMU_FAILURE_END_SAMPLE) {
        data.valid = false;
        }

    return data;
}