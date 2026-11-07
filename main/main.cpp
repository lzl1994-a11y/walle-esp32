#include <Arduino.h>
#include "afe_processor.h"
#include "display_app.h"
#include "esp_err.h"
#include "esp_log.h"
#include "i2s_mic_driver.h"
#include "usb_composite.h"

extern "C" void app_main(void)
{
    initArduino();
    ESP_ERROR_CHECK(usb_composite_init());
    ESP_ERROR_CHECK(afe_processor_init());
    ESP_ERROR_CHECK(i2s_mic_driver_init(afe_processor_get_feed_samples_per_channel()));
    ESP_ERROR_CHECK(i2s_mic_driver_start());
    ESP_ERROR_CHECK(afe_processor_start());
    ESP_ERROR_CHECK(display_app_start());
    ESP_LOGI("walle_esp32", "Audio, display and control tasks started");
}
