#ifndef GEO_H
#define GEO_H

#include "common/types.h"

void geodetic_to_ecef(double lat_deg, double lon_deg, double alt_m, ecef_position_t* out);
void ecef_to_geodetic(const ecef_position_t* ecef, geodetic_position_t* out);

void ned_to_ecef_delta(double ref_lat_deg, double ref_lon_deg,
                       double north_m, double east_m, double down_m,
                       double* dx, double* dy, double* dz);

#endif