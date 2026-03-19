#include "simulation/vehicle_model.h"

static vehicle_truth_t truth;
static const char* current_phase = "PAD";

void vehicle_model_init(void) {
    truth.time_s = 0.0f;
    truth.altitude_m = 0.0f;
    truth.velocity_z_mps = 0.0f;
    truth.acceleration_z_mps2 = 0.0f;
    truth.pitch_deg = 0.0f;
    truth.pitch_rate_dps = 0.0f;
    current_phase = "PAD";
}

void vehicle_model_step(float dt_s) {
    truth.time_s += dt_s;

    if (truth.time_s < 5.0f) {
        current_phase = "PAD";
        truth.acceleration_z_mps2 = 0.0f;
        truth.pitch_rate_dps = 0.0f;
    } else if (truth.time_s < 15.0f) {
        current_phase = "ASCENT";
        truth.acceleration_z_mps2 = 4.0f;
        truth.pitch_rate_dps = 1.2f;
    } else if (truth.time_s < 25.0f) {
        current_phase = "COAST";
        truth.acceleration_z_mps2 = -1.5f;
        truth.pitch_rate_dps = 0.3f;
    } else if (truth.time_s < 40.0f) {
        current_phase = "DESCENT";
        truth.acceleration_z_mps2 = -3.0f;
        truth.pitch_rate_dps = -0.8f;
    } else {
        current_phase = "LANDED";
        truth.acceleration_z_mps2 = 0.0f;
        truth.pitch_rate_dps = 0.0f;
    }

    if (truth.time_s < 40.0f) {
        truth.velocity_z_mps += truth.acceleration_z_mps2 * dt_s;
        truth.altitude_m += truth.velocity_z_mps * dt_s;
        truth.pitch_deg += truth.pitch_rate_dps * dt_s;

        if (truth.altitude_m < 0.0f) {
            truth.altitude_m = 0.0f;
            truth.velocity_z_mps = 0.0f;
        }
    } else {
        truth.altitude_m = 0.0f;
        truth.velocity_z_mps = 0.0f;
        truth.pitch_deg = 0.0f;
    }
}

const vehicle_truth_t* vehicle_model_get_truth(void) {
    return &truth;
}

const char* vehicle_model_get_phase(void) {
    return current_phase;
}