#pragma once
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "freertos/FreeRTOS.h"
using std::min;
extern uint32_t serialTestClock;
inline uint32_t millis() { return serialTestClock; }
inline void delay(unsigned int ms) { serialTestClock += ms; }
