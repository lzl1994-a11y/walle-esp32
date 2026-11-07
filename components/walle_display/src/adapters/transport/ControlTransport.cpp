#include "adapters/transport/ControlTransport.h"
#include "usb_composite.h"

namespace WallE {
size_t controlAvailable() {
  return usb_composite_cdc_read_available();
}
int controlRead() {
  uint8_t value = 0;
  return usb_composite_cdc_read(&value, 1) == 1 ? value : -1;
}
bool controlWrite(const uint8_t* data, size_t length) {
  return usb_composite_cdc_write(data, length, pdMS_TO_TICKS(100)) == ESP_OK;
}
}
