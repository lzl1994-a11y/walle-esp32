# 第三方与复用来源

- ESP-IDF 5.5.4 / Arduino-ESP32 3.3.12 / ESP-SR 2.4.6 / esp_tinyusb 2.2.0 / TinyUSB 0.19.0~3：使用官方组件及其原始许可，完整版本见 dependencies.lock。
- Arduino_GFX 1.5.6：来自显示项目的已安装 GFX Library for Arduino，源仓库 https://github.com/moononournation/Arduino_GFX 。保留源码中的原始署名与许可说明。
- 本地 Arduino_GFX 兼容补丁：SPI 时钟分频调用适配 Arduino 3.3 的实例参数；为 `Print::flush()` 增加无参转发，保留原 `flush(bool)` 行为；为多态 `Arduino_DataBus` 增加虚析构。JPEGDEC 构建声明已有 ESP-DSP 依赖以启用 S3 SIMD。
- JPEGDEC 1.8.4、AnimatedGIF 2.2.3：来自显示项目的已安装依赖；保留各组件 LICENSE 和源文件署名。
- walle_audio 和 walle_display 均按 2026-10-22 来源项目本地工作区核对：音频包含提交 5458555 后未提交的播放更新，显示当前 HEAD 为 c494b01。保留合并所需的构建、USB 通信适配和既有控制修复；配网解析器额外修复嵌入 NUL 的输入边界。来源指纹及验证见 docs/integration.md。
