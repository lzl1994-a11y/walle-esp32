"""Exercise production controller methods with a failing CDC and network queue.

Like the audio host tests, compile the actual functions with narrow hardware
substitutes; the full ESP-IDF build also checks their real class declarations.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

from test_audio_capture import ROOT, function


def main():
    compiler = shutil.which("g++")
    if not compiler:
        raise SystemExit("Host G++ is required")
    source = (ROOT / "components/walle_display/src/app/AppController.cpp").read_text(encoding="utf-8")
    prelude = r'''
#include "adapters/log/SerialOutput.h"
#include "ports/IInputPort.h"
#include "ports/INetworkConfigPort.h"
#include "domain/HostNetworkScreen.h"
#include <array>
#include <cassert>
#include <deque>
#include <iostream>

bool serialMutexHeld = false;
uint32_t serialTestClock = 0;
static bool transportReady = true;
static int writesBeforeFailure = -1;
static std::vector<std::string> output;
namespace WallE {
bool controlWrite(const uint8_t* data, size_t length) {
  assert(serialMutexHeld);
  if (!transportReady || writesBeforeFailure == 0) return false;
  if (writesBeforeFailure > 0) --writesBeforeFailure;
  output.emplace_back(reinterpret_cast<const char*>(data), length);
  return true;
}
class NetworkResults : public INetworkConfigPort {
 public:
  std::deque<std::string> results;
  size_t dequeued = 0;
  bool handleSerialCommand(const uint8_t*, size_t, char*, size_t, bool&) override { return false; }
  void acknowledgeApplyOutput() override {}
  bool pollSerialResponse(char* response, size_t capacity) override {
    if (results.empty()) return false;
    assert(results.front().size() < capacity);
    memcpy(response, results.front().c_str(), results.front().size() + 1);
    results.pop_front();
    ++dequeued;
    return true;
  }
};
class AppController {
 public:
  enum class ScreenMode { Power, Chat, CameraStreaming, CameraHold, NetworkSetup };
  struct Display {
    int powerDraws = 0, hostDraws = 0;
    uint8_t shownPower = 0;
    std::string shownHost;
    uint16_t shownPort = 0;
    void showPower(uint8_t percent) { ++powerDraws; shownPower = percent; }
    void showNetworkHost(const char* host, uint16_t port) {
      ++hostDraws; shownHost = host; shownPort = port;
    }
  } display_;
  ScreenMode screenMode_ = ScreenMode::Power;
  HostNetworkScreen networkScreen_;
  uint32_t networkDoneAtMs_ = 0;
  uint8_t powerPercent_ = 75;
  explicit AppController(INetworkConfigPort& network) : networkConfig_(network) {}
  bool flushNetworkResponses();
  void updateNetworkScreen();
 private:
  INetworkConfigPort& networkConfig_;
  char pendingNetworkResponse_[512] = {0};
};
'''
    assertions = r'''
}  // namespace WallE

static bool parse(const std::vector<std::string>& fields, std::array<int32_t, 15>& values) {
  std::string command = "pca9685:";
  for (size_t i = 0; i < fields.size(); ++i) {
    if (i) command += ',';
    command += fields[i];
  }
  return WallE::parsePca9685({reinterpret_cast<const uint8_t*>(command.data()), command.size()}, values.data());
}

int main() {
  WallE::NetworkResults network;
  WallE::AppController controller(network);
  const std::string first = "NETCFG:RESULT:42|APPLY|2|0";
  const std::string second = "NETCFG:RESULT:43|APPLY|6|9";
  const std::string third = "NETCFG:RESULT:44|APPLY|6|10";
  assert(!controller.flushNetworkResponses() && output.empty());
  network.results = {first, second};
  transportReady = false;
  assert(!controller.flushNetworkResponses());
  assert(!controller.flushNetworkResponses());
  assert(network.dequeued == 1 && network.results.size() == 1 && output.empty());
  network.results.push_back(third);
  transportReady = true;
  assert(controller.flushNetworkResponses());
  assert((output == std::vector<std::string>{first+"\r\n", second+"\r\n", third+"\r\n"}));
  assert(network.results.empty() && network.dequeued == 3);
  assert(!controller.flushNetworkResponses() && output.size() == 3);
  // A successful line followed by a failed line must not be replayed twice.
  output.clear();
  network.results = {first, second, third};
  writesBeforeFailure = 1;
  assert(controller.flushNetworkResponses());
  assert(output.size() == 1 && network.results.size() == 1);
  writesBeforeFailure = -1;
  assert(controller.flushNetworkResponses());
  assert((output == std::vector<std::string>{first+"\r\n", second+"\r\n", third+"\r\n"}));

  std::array<int32_t, 15> values;
  std::vector<std::string> fields(15, "6500");
  fields[0] = "-2147483648";
  fields[1] = "2147483647";
  fields[2] = "-1";
  fields[3] = "-0";
  fields[4] = " 65535 ";
  assert(parse(fields, values));
  assert(values[0] == INT32_MIN && values[1] == INT32_MAX && values[2] == -1);
  assert(values[3] == 0 && values[4] == 65535 && values[14] == 6500);
  const std::vector<std::string> invalid = {
    "2147483648", "-2147483649", "4294970096", "4294973796", "-", "--1", "+1", "", "bad", std::string(490, '9')
  };
  for (size_t position : {size_t(0), size_t(7), size_t(14)}) {
    for (const auto& bad : invalid) {
      fields.assign(15, "2800");
      fields[position] = bad;
      values.fill(6500);
      const auto original = values;
      assert(!parse(fields, values));
      assert(values == original);  // Rejection must be atomic across the batch.
    }
  }
  for (size_t count : {size_t(14), size_t(16)}) {
    fields.assign(count, "2800");
    const auto original = values;
    assert(!parse(fields, values) && values == original);
  }
  assert(!WallE::parsePca9685({nullptr, 0}, values.data()));
  assert(!WallE::parsePca9685({nullptr, 0}, nullptr));

  for (const auto* state : {"setup", "connecting", "connected", "syncing", "partial"}) {
    controller.screenMode_ = WallE::AppController::ScreenMode::NetworkSetup;
    strcpy(controller.networkScreen_.state, state);
    controller.networkDoneAtMs_ = 100;
    serialTestClock = 10000;
    controller.updateNetworkScreen();
    assert(controller.screenMode_ == WallE::AppController::ScreenMode::NetworkSetup);
    assert(controller.display_.powerDraws == 0 && controller.display_.hostDraws == 0);
  }
  strcpy(controller.networkScreen_.state, "done");
  strcpy(controller.networkScreen_.ip, "192.168.0.5");
  controller.networkScreen_.port = 8080;
  for (uint32_t start : {uint32_t(100), UINT32_MAX - uint32_t(100)}) {
    controller.display_ = {};
    controller.screenMode_ = WallE::AppController::ScreenMode::NetworkSetup;
    controller.networkDoneAtMs_ = start;
    serialTestClock = start + 2999;
    controller.updateNetworkScreen();
    assert(controller.screenMode_ == WallE::AppController::ScreenMode::NetworkSetup);
    assert(controller.display_.powerDraws == 0);
    serialTestClock += 1;
    controller.updateNetworkScreen();
    assert(controller.screenMode_ == WallE::AppController::ScreenMode::Power);
    assert(controller.display_.powerDraws == 1 && controller.display_.shownPower == 75);
    assert(controller.display_.hostDraws == 1 && controller.display_.shownHost == "192.168.0.5");
    assert(controller.display_.shownPort == 8080);
    controller.updateNetworkScreen();
    assert(controller.display_.powerDraws == 1 && controller.display_.hostDraws == 1);
  }
  std::cout << "PASS: NETCFG delivery, atomic int32 PCA9685 bounds, provisioning exit timing and clock wrap\n";
}
'''
    names = ("startsWithIgnoreCase", "parsePca9685", "flushNetworkResponses", "updateNetworkScreen")
    program = prelude + "\n" + "\n".join(function(source, name) for name in names) + assertions
    with tempfile.TemporaryDirectory(prefix="walle-control-") as folder:
        src = Path(folder) / "control.cpp"
        executable = Path(folder) / "control.exe"
        src.write_text(program, encoding="utf-8")
        subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        "-I" + str(ROOT / "tools/serial_output_test"),
                        "-I" + str(ROOT / "components/walle_display/src"),
                        str(src), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
