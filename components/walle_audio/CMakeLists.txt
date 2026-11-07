idf_component_register(
    SRCS "i2s_mic_driver.c" "afe_processor.c" "usb_composite.c"
    INCLUDE_DIRS "."
    REQUIRES esp_driver_i2s esp_rom esp_timer soc esp-sr esp_tinyusb espressif__tinyusb)
idf_build_get_property(build_components BUILD_COMPONENTS)
foreach(tusb_component IN ITEMS espressif__tinyusb tinyusb)
    if(${tusb_component} IN_LIST build_components)
        idf_component_get_property(tusb_lib ${tusb_component} COMPONENT_LIB)
        target_include_directories(${tusb_lib} BEFORE PUBLIC "${CMAKE_CURRENT_LIST_DIR}")
    endif()
endforeach()
