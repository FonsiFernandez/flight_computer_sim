#include "comms/command.h"
#include "common/types.h"
#include "test_utils.h"

void test_command_parse_status(void) {
    command_t cmd = command_parse("status");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_STATUS, cmd.type);
}

void test_command_parse_reset_warnings(void) {
    command_t cmd = command_parse("reset_warnings");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_RESET_WARNINGS, cmd.type);
}

void test_command_parse_reset_all(void) {
    command_t cmd = command_parse("reset_all");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_RESET_ALL, cmd.type);
}

void test_command_parse_force_nominal(void) {
    command_t cmd = command_parse("force_nominal");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_FORCE_NOMINAL, cmd.type);
}

void test_command_parse_force_safe(void) {
    command_t cmd = command_parse("force_safe");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_FORCE_SAFE, cmd.type);
}

void test_command_parse_help(void) {
    command_t cmd = command_parse("help");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_HELP, cmd.type);
}

void test_command_parse_quit(void) {
    command_t cmd = command_parse("quit");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_QUIT, cmd.type);
}

void test_command_parse_empty_string(void) {
    command_t cmd = command_parse("");

    TEST_ASSERT_TRUE(cmd.valid);
    TEST_ASSERT_EQUAL_INT(COMMAND_NONE, cmd.type);
}

void test_command_parse_unknown_command(void) {
    command_t cmd = command_parse("foobar");

    TEST_ASSERT_FALSE(cmd.valid);
}

void test_command_parse_null_is_invalid(void) {
    command_t cmd = command_parse(NULL);

    TEST_ASSERT_FALSE(cmd.valid);
}