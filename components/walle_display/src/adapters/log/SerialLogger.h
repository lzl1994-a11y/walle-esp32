#pragma once

#include "config/Config.h"
#include "adapters/log/SerialOutput.h"
#include "ports/ILogger.h"
#include <Arduino.h>

namespace WallE {

/**
 * 中文：通过共享 TinyUSB CDC 输出日志。
 * English: Logger implementation using the shared TinyUSB CDC.
 */
class SerialLogger : public ILogger {
 public:
  /**
   * 中文：保留日志初始化接口；USB 由应用入口统一启动。
   * English: Preserves the logger initialization interface; the application entry owns USB startup.
   *
   * @param 无 / None.
   * @return 无 / None.
   */
  void begin() override {
    // TinyUSB is initialized by app_main before the display task starts.
  }

  /**
   * 中文：输出 INFO 级别日志。
   * English: Outputs an INFO-level log.
   *
   * @param message 中文：日志文本。
   *                English: Log text.
   * @return 无 / None.
   */
  void info(const char* message) override { log("INFO", message); }

  /**
   * 中文：输出 WARN 级别日志。
   * English: Outputs a WARN-level log.
   *
   * @param message 中文：日志文本。
   *                English: Log text.
   * @return 无 / None.
   */
  void warn(const char* message) override { log("WARN", message); }

  /**
   * 中文：输出 ERROR 级别日志。
   * English: Outputs an ERROR-level log.
   *
   * @param message 中文：日志文本。
   *                English: Log text.
   * @return 无 / None.
   */
  void error(const char* message) override { log("ERROR", message); }

 private:
  /**
   * 中文：按统一格式 [LEVEL] message 写入串口。
   * English: Writes a Serial line in the unified format [LEVEL] message.
   *
   * @param level 中文：日志级别文本，例如 INFO。
   *              English: Log level text such as INFO.
   * @param message 中文：日志正文。
   *                English: Log body.
   * @return 无 / None.
   */
  void log(const char* level, const char* message) {
    serialLogLine(level, message);
  }
};

}  // namespace WallE
