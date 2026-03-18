#ifndef LOGGER_H
#define LOGGER_H

void logger_init(void);
void logger_info(const char *msg);
void logger_error(const char *msg);
void logger_warn(const char *msg);

#endif