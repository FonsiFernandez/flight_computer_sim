#include "time_port.h"

#ifdef _WIN32
#include <windows.h>

uint64_t time_now_ms(void) {
    return GetTickCount64();
}

void time_sleep_ms(uint32_t ms) {
    Sleep(ms);
}

#else
#include <time.h>
#include <unistd.h>

uint64_t time_now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000ULL);
}

void time_sleep_ms(uint32_t ms) {
    usleep(ms * 1000);
}
#endif