#ifndef FAULT_MANAGER_H
#define FAULT_MANAGER_H

#include "common/types.h"

void fault_manager_init(void);
system_mode_t fault_manager_update(health_status_t health, system_mode_t current_mode);
void fault_manager_process_manual_reset_warnings(void);
void fault_manager_process_manual_reset_all(void);
void fault_manager_force_mode(system_mode_t mode);

#endif