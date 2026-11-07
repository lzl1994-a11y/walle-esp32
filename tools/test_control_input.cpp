#include "adapters/input/SerialInputPort.h"
#include <cassert>
#include <deque>
#include <iostream>
#include <string>

bool serialMutexHeld = false;
uint32_t serialTestClock = 0;
static std::deque<uint8_t> incoming;
namespace WallE {
size_t controlAvailable() { return incoming.size(); }
int controlRead() {
  if (incoming.empty()) return -1;
  const int ch=incoming.front(); incoming.pop_front(); return ch;
}
bool controlWrite(const uint8_t*, size_t) { assert(serialMutexHeld); return true; }
}
static void feed(const std::string& value) {
  for (unsigned char ch:value) incoming.push_back(ch);
}
int main() {
  WallE::SerialInputPort input;
  WallE::InputPacket packet;
  input.begin();
  feed("getname:WHO_"); assert(!input.poll(packet));
  feed("ARE_YOU\r\neye:blink\n");
  assert(input.poll(packet));
  assert(std::string(reinterpret_cast<const char*>(packet.data),packet.length)=="getname:WHO_ARE_YOU");
  assert(input.poll(packet));
  assert(std::string(reinterpret_cast<const char*>(packet.data),packet.length)=="eye:blink");
  assert(!input.poll(packet));
  feed(std::string(512,'x')+"\n");
  assert(input.poll(packet) && packet.length==512);
  feed(std::string(513,'x')+"\neye:blink\n");
  assert(input.poll(packet));
  assert(std::string(reinterpret_cast<const char*>(packet.data),packet.length)=="eye:blink");
  feed("zoom"); assert(!input.poll(packet));
  serialTestClock+=249; assert(!input.poll(packet));
  serialTestClock+=1; assert(input.poll(packet) && packet.length==4);
  feed(std::string(600,'x')); assert(!input.poll(packet));
  serialTestClock+=250; assert(!input.poll(packet));
  feed("zoom\n"); assert(input.poll(packet) && packet.length==4);
  // No intermediate poll while CDC output keeps the control task busy.
  feed(std::string(513, 'x')); assert(!input.poll(packet));
  serialTestClock += 300;
  feed("getname:WHO_ARE_YOU\n");
  assert(input.poll(packet));
  assert(std::string(reinterpret_cast<const char*>(packet.data), packet.length) == "getname:WHO_ARE_YOU");
  // A tail arriving before the timeout still belongs to the rejected packet.
  feed(std::string(513, 'x')); assert(!input.poll(packet));
  serialTestClock += 249;
  feed("tail\nzoom\n");
  assert(input.poll(packet) && packet.length == 4);
  assert(std::string(reinterpret_cast<const char*>(packet.data), packet.length) == "zoom");
  serialTestClock = UINT32_MAX - 100;
  feed(std::string(513, 'x')); assert(!input.poll(packet));
  serialTestClock += 250;
  feed("zoom\n");
  assert(input.poll(packet) && packet.length == 4);
  feed("discard"); input.drain(); assert(!input.poll(packet));
  std::cout << "PASS: CDC fragmentation, CR/LF, 512-byte lines, oversize recovery, delayed polls and clock wrap\n";
}
