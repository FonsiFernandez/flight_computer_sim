#include "logger.h"
#include "uart_port.h"
#include "time_port.h"

#include <stdio.h>
#include <stdint.h>

static uint64_t logger_start_ms = 0;

void logger_init(void) {
    logger_start_ms = time_now_ms();
}

static void logger_log(const char *level, const char *msg) {
    char buffer[512];
    uint64_t now = time_now_ms();
    uint64_t elapsed = now - logger_start_ms;

    snprintf(buffer, sizeof(buffer),
             "[%s][T+%llu ms] %s",
             level,
             (unsigned long long)elapsed,
             msg);

    uart_send_line(buffer);
}

void logger_info(const char *msg) {
    logger_log("INFO", msg);
}

void logger_error(const char *msg) {
    logger_log("ERROR", msg);
}

void logger_warn(const char *msg) {
    logger_log("WARN", msg);
}