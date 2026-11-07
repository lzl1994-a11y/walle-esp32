#include "adapters/log/SerialOutput.h"
#include <cassert>
#include <iostream>

bool serialMutexHeld = false;
uint32_t serialTestClock = 0;
static bool transportReady = true;
static std::vector<std::string> output;
namespace WallE {
bool controlWrite(const uint8_t* data, size_t length) {
  assert(serialMutexHeld);
  if (!transportReady) return false;
  output.emplace_back(reinterpret_cast<const char*>(data), length);
  return true;
}
}
static void expectLine(const std::string& text) {
  assert(!serialMutexHeld && output.size() == 1 && output[0] == text);
  output.clear();
}
int main() {
  assert(WallE::serialPrintln("EYE:OK"));
  expectLine("EYE:OK\r\n");
  assert(WallE::serialWriteLine(nullptr, 100));
  expectLine("\r\n");
  std::string oversized(600, 'x');
  assert(WallE::serialWriteLine(oversized.data(), oversized.size()));
  expectLine(std::string(512, 'x') + "\r\n");
  WallE::serialLogLine("ERROR", "test");
  expectLine("[ERROR] test\r\n");
  transportReady = false;
  assert(!WallE::serialPrintln("NETCFG:ACK"));
  assert(!serialMutexHeld && output.empty());
  std::cout << "PASS: complete CDC lines, output lock, length bounds and delivery errors\n";
}
