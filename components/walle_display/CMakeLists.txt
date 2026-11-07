idf_component_register(
    SRCS
        "core/adapters/display/Esp32AsyncDmaWriter.cpp"
        "core/adapters/display/Gc9a01Panel.cpp"
        "core/adapters/display/GifPlayer.cpp"
        "core/adapters/display/ScreenFontFlash.cpp"
        "core/adapters/display/St7789Panel.cpp"
        "core/adapters/display/TextRenderer.cpp"
        "src/adapters/display/Gc9a01EyeDisplay.cpp"
        "src/adapters/display/St7789DisplayPort.cpp"
        "src/adapters/input/SerialInputPort.cpp"
        "src/adapters/network/NetworkConfigStore.cpp"
        "src/adapters/network/WifiImageStreamClient.cpp"
        "src/adapters/pca9685/Pca9685Driver.cpp"
        "src/adapters/transport/ControlTransport.cpp"
        "src/app/AppController.cpp"
        "src/display_app.cpp"
        "src/domain/ChatSession.cpp"
        "src/domain/EyeRenderer.cpp"
    INCLUDE_DIRS "src" "core"
    REQUIRES arduino-esp32 walle_audio arduino_gfx jpegdec animatedgif
        esp_driver_spi esp_driver_gpio esp_wifi
    PRIV_REQUIRES espressif__network_provisioning)
