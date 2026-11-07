#pragma once

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#include "esp_err.h"
#include "freertos/FreeRTOS.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t usb_composite_init(void);
esp_err_t usb_composite_uac_write(const int16_t *pcm, size_t byte_len, TickType_t ticks_to_wait);
size_t usb_composite_cdc_read_available(void);
size_t usb_composite_cdc_read(uint8_t *data, size_t capacity);
/* Serialize callers; writes enqueue a complete message or time out. */
esp_err_t usb_composite_cdc_write(const uint8_t *data, size_t length, TickType_t ticks_to_wait);
esp_err_t usb_composite_cdc_write_str(const char *text, TickType_t ticks_to_wait);
bool usb_composite_is_mounted(void);
bool usb_composite_uac_is_streaming(void);
bool usb_composite_cdc_is_connected(void);
uint8_t usb_composite_cdc_get_line_state(void);
uint32_t usb_composite_cdc_write_available(void);

#ifdef __cplusplus
}
#endif
