idf_component_register(
    SRCS "src/Arduino_G.cpp" "src/Arduino_DataBus.cpp" "src/Arduino_GFX.cpp" "src/Arduino_TFT.cpp"
         "src/databus/Arduino_ESP32SPIDMA.cpp"
         "src/display/Arduino_ST7789.cpp" "src/display/Arduino_GC9A01.cpp"
    INCLUDE_DIRS "src"
    REQUIRES arduino-esp32 esp_driver_spi esp_driver_gpio esp_lcd)
