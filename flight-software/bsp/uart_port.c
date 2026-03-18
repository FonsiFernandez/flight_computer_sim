#include "uart_port.h"
#include <stdio.h>

void uart_send_line(const char *msg) {
    printf("%s\n", msg);
    fflush(stdout);
}