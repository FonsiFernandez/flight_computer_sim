#include "simulation/vehicle_model.h"
#include "simulation/geo.h"

static vehicle_truth_t truth;
static const char* current_phase = "PAD";

static geodetic_position_t origin_geo;
static ecef_position_t current_ecef;

void vehicle_model_init(void) {
    truth.time_s = 0.0f;

    origin_geo.lat_deg = 5.236;
    origin_geo.lon_deg = -52.768;
    origin_geo.alt_m = 0.0;

    geodetic_to_ecef(origin_geo.lat_deg, origin_geo.lon_deg, origin_geo.alt_m, &current_ecef);

    truth.lat_deg = origin_geo.lat_deg;
    truth.lon_deg = origin_geo.lon_deg;
    truth.alt_m = origin_geo.alt_m;

    truth.ecef_x_m = current_ecef.x_m;
    truth.ecef_y_m = current_ecef.y_m;
    truth.ecef_z_m = current_ecef.z_m;

    truth.vel_north_mps = 0.0;
    truth.vel_east_mps = 0.0;
    truth.vel_down_mps = 0.0;

    truth.acc_north_mps2 = 2.0;
    truth.acc_east_mps2 = 0.8;
    truth.acc_down_mps2 = 0.0;

    truth.pitch_deg = 0.0f;
    truth.pitch_rate_dps = 0.0f;

    truth.altitude_m = 0.0f;
    truth.velocity_z_mps = 0.0f;
    truth.acceleration_z_mps2 = 0.0f;

    current_phase = "PAD";
}

void vehicle_model_step(float dt_s) {
    truth.time_s += dt_s;

    if (truth.time_s < 5.0f) {
        current_phase = "PAD";
        truth.acc_north_mps2 = 0.0;
        truth.acc_east_mps2 = 0.0;
        truth.acc_down_mps2 = 0.0;
        truth.pitch_rate_dps = 0.0f;
    } else if (truth.time_s < 15.0f) {
        current_phase = "ASCENT";
        truth.acc_north_mps2 = 2.5;
        truth.acc_east_mps2 = 1.0;
        truth.acc_down_mps2 = -4.0;
        truth.pitch_rate_dps = 1.2f;
    } else if (truth.time_s < 25.0f) {
        current_phase = "COAST";
        truth.acc_north_mps2 = 0.4;
        truth.acc_east_mps2 = 0.2;
        truth.acc_down_mps2 = 1.5;
        truth.pitch_rate_dps = 0.3f;
    } else if (truth.time_s < 40.0f) {
        current_phase = "DESCENT";
        truth.acc_north_mps2 = -0.8;
        truth.acc_east_mps2 = -0.2;
        truth.acc_down_mps2 = 3.0;
        truth.pitch_rate_dps = -0.8f;
    } else {
        current_phase = "LANDED";
        truth.acc_north_mps2 = 0.0;
        truth.acc_east_mps2 = 0.0;
        truth.acc_down_mps2 = 0.0;
        truth.pitch_rate_dps = 0.0f;
    }

    if (truth.time_s < 40.0f) {
        truth.vel_north_mps += truth.acc_north_mps2 * dt_s;
        truth.vel_east_mps += truth.acc_east_mps2 * dt_s;
        truth.vel_down_mps += truth.acc_down_mps2 * dt_s;

        double dn = truth.vel_north_mps * dt_s;
        double de = truth.vel_east_mps * dt_s;
        double dd = truth.vel_down_mps * dt_s;

        double dx, dy, dz;
        ned_to_ecef_delta(truth.lat_deg, truth.lon_deg, dn, de, dd, &dx, &dy, &dz);

        current_ecef.x_m += dx;
        current_ecef.y_m += dy;
        current_ecef.z_m += dz;

        geodetic_position_t geo;
        ecef_to_geodetic(&current_ecef, &geo);

        truth.lat_deg = geo.lat_deg;
        truth.lon_deg = geo.lon_deg;
        truth.alt_m = geo.alt_m;

        truth.ecef_x_m = current_ecef.x_m;
        truth.ecef_y_m = current_ecef.y_m;
        truth.ecef_z_m = current_ecef.z_m;

        truth.pitch_deg += truth.pitch_rate_dps * dt_s;

        truth.altitude_m = (float)truth.alt_m;
        truth.velocity_z_mps = (float)(-truth.vel_down_mps);
        truth.acceleration_z_mps2 = (float)(-truth.acc_down_mps2);

        if (truth.altitude_m < 0.0f) {
            truth.altitude_m = 0.0f;
            truth.alt_m = 0.0;
            truth.vel_down_mps = 0.0;
        }
    } else {
        truth.vel_north_mps = 0.0;
        truth.vel_east_mps = 0.0;
        truth.vel_down_mps = 0.0;
        truth.pitch_deg = 0.0f;
        truth.altitude_m = 0.0f;
        truth.alt_m = 0.0;
    }
}

const vehicle_truth_t* vehicle_model_get_truth(void) {
    return &truth;
}

const char* vehicle_model_get_phase(void) {
    return current_phase;
}