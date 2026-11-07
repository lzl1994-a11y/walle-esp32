#pragma once

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <string.h>
#include "adapters/transport/ControlTransport.h"

namespace WallE {

// One mutex is shared by logs and protocol replies, so no two tasks can leave
// interleaved fragments on USB serial. A mutex is deliberately used instead
// of a portMUX: Serial writes can block and must never run in a spinlock.
inline SemaphoreHandle_t serialOutputMutex() {
  static SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
  return mutex;
}

inline bool serialWriteLine(const char* text, size_t length) {
  constexpr size_t kMaxLineBytes = 512;
  if (text == nullptr) { text = ""; length = 0; }
  length = min(length, kMaxLineBytes);
  char line[kMaxLineBytes + 2] = {};
  if (length > 0) memcpy(line, text, length);
  line[length] = '\r';
  line[length + 1] = '\n';
  SemaphoreHandle_t mutex = serialOutputMutex();
  if (mutex == nullptr || xSemaphoreTake(mutex, pdMS_TO_TICKS(100)) != pdTRUE) return false;
  const bool sent = controlWrite(reinterpret_cast<const uint8_t*>(line), length + 2);
  xSemaphoreGive(mutex);
  return sent;
}

inline bool serialPrintln(const char* text) {
  return serialWriteLine(text, strnlen(text == nullptr ? "" : text, 512));
}

inline void serialLogLine(const char* level, const char* message) {
  char line[512] = {};
  const int written = snprintf(line, sizeof(line), "[%s] %s",
                               level == nullptr ? "" : level,
                               message == nullptr ? "" : message);
  const size_t length = written <= 0 ? 0 : min(
      static_cast<size_t>(written), sizeof(line) - 1);
  serialWriteLine(line, length);
}

}  // namespace WallE
