#include "simulation/geo.h"
#include <math.h>

#define EARTH_RADIUS_M 6371000.0
#define DEG2RAD(x) ((x) * M_PI / 180.0)
#define RAD2DEG(x) ((x) * 180.0 / M_PI)

void geodetic_to_ecef(double lat_deg, double lon_deg, double alt_m, ecef_position_t* out) {
    double lat = DEG2RAD(lat_deg);
    double lon = DEG2RAD(lon_deg);
    double r = EARTH_RADIUS_M + alt_m;

    out->x_m = r * cos(lat) * cos(lon);
    out->y_m = r * cos(lat) * sin(lon);
    out->z_m = r * sin(lat);
}

void ecef_to_geodetic(const ecef_position_t* ecef, geodetic_position_t* out) {
    double r = sqrt(ecef->x_m * ecef->x_m + ecef->y_m * ecef->y_m + ecef->z_m * ecef->z_m);
    double lat = asin(ecef->z_m / r);
    double lon = atan2(ecef->y_m, ecef->x_m);

    out->lat_deg = RAD2DEG(lat);
    out->lon_deg = RAD2DEG(lon);
    out->alt_m = r - EARTH_RADIUS_M;
}

void ned_to_ecef_delta(double ref_lat_deg, double ref_lon_deg,
                       double north_m, double east_m, double down_m,
                       double* dx, double* dy, double* dz) {
    double lat = DEG2RAD(ref_lat_deg);
    double lon = DEG2RAD(ref_lon_deg);

    double n_x = -sin(lat) * cos(lon);
    double n_y = -sin(lat) * sin(lon);
    double n_z =  cos(lat);

    double e_x = -sin(lon);
    double e_y =  cos(lon);
    double e_z =  0.0;

    double d_x = -cos(lat) * cos(lon);
    double d_y = -cos(lat) * sin(lon);
    double d_z = -sin(lat);

    *dx = north_m * n_x + east_m * e_x + down_m * d_x;
    *dy = north_m * n_y + east_m * e_y + down_m * d_y;
    *dz = north_m * n_z + east_m * e_z + down_m * d_z;
}