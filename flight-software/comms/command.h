#ifndef COMMAND_H
#define COMMAND_H

#include "common/types.h"

void command_init(void);
command_t command_poll(void);
command_t command_parse(const char *line);

#endif