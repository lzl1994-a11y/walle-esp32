#pragma once
#include <cstdint>
using BaseType_t = int;
using UBaseType_t = unsigned;
constexpr uint32_t portMAX_DELAY = UINT32_MAX;
constexpr int pdTRUE = 1;
#define pdMS_TO_TICKS(ms) (ms)
