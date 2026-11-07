idf_component_register(SRCS "src/JPEGDEC.cpp" "src/s3_simd_420.S"
    "src/s3_simd_444.S" "src/s3_simd_dequant.S"
    INCLUDE_DIRS "src" REQUIRES arduino-esp32 PRIV_REQUIRES esp-dsp)
