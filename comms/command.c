#include "command.h"

#include <string.h>
#include <stdio.h>

#ifdef _WIN32
#include <conio.h>
#endif

void command_init(void) {
}

static command_t parse_command(const char *line) {
    command_t cmd;
    cmd.type = COMMAND_NONE;
    cmd.valid = true;

    if (strcmp(line, "status") == 0) {
        cmd.type = COMMAND_STATUS;
    } else if (strcmp(line, "reset_warnings") == 0) {
        cmd.type = COMMAND_RESET_WARNINGS;
    } else if (strcmp(line, "reset_all") == 0) {
        cmd.type = COMMAND_RESET_ALL;
    } else if (strcmp(line, "force_nominal") == 0) {
        cmd.type = COMMAND_FORCE_NOMINAL;
    } else if (strcmp(line, "force_safe") == 0) {
        cmd.type = COMMAND_FORCE_SAFE;
    } else if (strcmp(line, "help") == 0) {
        cmd.type = COMMAND_HELP;
    } else if (strcmp(line, "quit") == 0) {
        cmd.type = COMMAND_QUIT;
    } else if (strlen(line) == 0) {
        cmd.type = COMMAND_NONE;
    } else {
        cmd.valid = false;
    }

    return cmd;
}

command_t command_poll(void) {
    command_t none = { COMMAND_NONE, true };

#ifdef _WIN32
    if (!_kbhit()) {
        return none;
    }

    char buffer[128];
    if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
        return none;
    }
#else
    return none;
#endif

    size_t len = strlen(buffer);
    while (len > 0 && (buffer[len - 1] == '\n' || buffer[len - 1] == '\r')) {
        buffer[len - 1] = '\0';
        len--;
    }

    return parse_command(buffer);
}