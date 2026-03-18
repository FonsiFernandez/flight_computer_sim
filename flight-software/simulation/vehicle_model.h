#ifndef VEHICLE_MODEL_H
#define VEHICLE_MODEL_H

#include "common/types.h"

void vehicle_model_init(void);
void vehicle_model_step(float dt_s);
const vehicle_truth_t* vehicle_model_get_truth(void);
const char* vehicle_model_get_phase(void);

#endif