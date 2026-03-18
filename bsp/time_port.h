#ifndef TIME_PORT_H
#define TIME_PORT_H

#include <stdint.h>

uint64_t time_now_ms(void);
void time_sleep_ms(uint32_t ms);

#endif