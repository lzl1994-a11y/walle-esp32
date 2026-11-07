#pragma once
#include <stddef.h>
#include <stdint.h>

namespace WallE {
// The command parser and UI do not depend on the physical transport.
size_t controlAvailable();
int controlRead();
bool controlWrite(const uint8_t* data, size_t length);
}
