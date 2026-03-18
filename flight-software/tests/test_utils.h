#ifndef TEST_UTILS_H
#define TEST_UTILS_H

#include <stdio.h>

extern int tests_failed;

#define TEST_ASSERT_TRUE(condition) do { \
if (!(condition)) { \
printf("  Assertion failed: %s (%s:%d)\n", #condition, __FILE__, __LINE__); \
tests_failed++; \
return; \
} \
} while(0)

#define TEST_ASSERT_FALSE(condition) TEST_ASSERT_TRUE(!(condition))

#define TEST_ASSERT_EQUAL_INT(expected, actual) do { \
if ((expected) != (actual)) { \
printf("  Assertion failed: expected=%d actual=%d (%s:%d)\n", \
(expected), (actual), __FILE__, __LINE__); \
tests_failed++; \
return; \
} \
} while(0)

#endif