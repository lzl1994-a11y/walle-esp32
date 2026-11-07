cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
set(PROJECT_VER "0.1.0")
project(walle_esp32)

# TinyUSB UAC/CDC is owned by walle_audio, not by Arduino USB/HWCDC.
idf_build_set_property(COMPILE_DEFINITIONS "ARDUINO_USB_CDC_ON_BOOT=0;ARDUINO_USB_MODE=0;CORE_DEBUG_LEVEL=0" APPEND)

# esp_tinyusb and Arduino share CONFIG_TINYUSB_CDC_ENABLED. Arduino's CDC
# implementation tests that symbol even when its own USB stack is disabled.
# Keep the external stack as the sole owner of the CDC callbacks.
idf_component_get_property(arduino_lib espressif__arduino-esp32 COMPONENT_LIB)
get_target_property(arduino_sources ${arduino_lib} SOURCES)
list(FILTER arduino_sources EXCLUDE REGEX "(^|/)USBCDC\\.cpp$")
set_property(TARGET ${arduino_lib} PROPERTY SOURCES "${arduino_sources}")
