#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include "types.h"

void state_machine_init(void);
system_mode_t state_machine_get_mode(void);
void state_machine_set_mode(system_mode_t mode);
const char* state_machine_get_mode_string(system_mode_t mode);

#endif