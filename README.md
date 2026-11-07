# WALL-E ESP32 单板集成固件

ESP32-S3（16 MB Flash、8 MB OPI PSRAM）统一运行 USB 收音/播放、胸屏、双眼、Wi-Fi JPEG 预览和 PCA9685 控制。

## 合并来源与保留功能

- 音频来源：`ESP32-S3-4-Mic-UAC-Array-Sound-Localization`，已按 2026-10-22 本地工作区核对，包含提交 `5458555` 后尚未提交的播放更新。
- 显示来源：`wall-e-tft`，已按 2026-10-22 本地工作区同步，当前 HEAD 为 `c494b01`。
- 两个来源均以本地工作区为准，包含未提交修改；提交号仅供追溯。保留合并项目专用引脚、共享 CDC 适配和已验证的控制修复，来源指纹见合并记录。
- 复用两个项目的现有驱动、AppController、EyeRenderer、字库/文本渲染、JPEG/TCP 客户端、NETCFG v2 与 PCA9685 实现；源项目未改动。
- 声源定位已删除；VAD 与其 48→16 kHz 抽取代码保留，默认 `AFE_ENABLE_VAD=0`。当前没有启用 AEC、降噪或自动增益。
- 仍采集双麦，USB 麦克风输出 Mic0 左时隙、48 kHz/16-bit 单声道，固定 2 倍增益并限幅。
- USB 扬声器输入 48 kHz/16-bit 双声道，经原有 4 倍增益与限幅送 PCM5102，保留 I2S 持续时钟和防杂音的数据对齐处理。
- I2S1 的 RX 先初始化并持续提供 BCLK/WS、MCLK，TX 作为全双工从通道，在第一包有效播放数据到来时启用；写入最多等待 100 ms，错误和不完整写入向上返回。
- 胸屏 ST7789、双眼 GC9A01、实时眼睛参数/动作、聊天/电量界面、字库、Wi-Fi/TCP JPEG 预览与舵机命令保持原功能。
- 上位机配网引导界面支持热点、连接/同步进度、失败重试提示，成功后 3 秒返回电量页。通过共享 CDC 接收 `hostnet:`，协议见 [配网屏幕说明](docs/display/host-wifi.md)。

## 引脚：只改音频

显示项目的 GPIO 配置完整保留在 `components/walle_display/src/config/Config.h`。

开发板插接底板的完整 GPIO 接线、双麦/DAC 连接和独立供电 USB 预留见 [画板引脚与接线表](docs/hardware-pinout.md)。GPIO 编号不是开发板排针序号，排针封装及供电隔离需按开发板型号核对。

| 外设 | 信号 | GPIO |
| --- | --- | --- |
| 胸屏/字库 | SCK / MOSI / MISO | 18 / 17 / 16 |
| 胸屏 | DC / RST / CS | 13 / 15 / 14 |
| 字库 Flash | CS | 11 |
| 双眼（共用片选） | SCK / MOSI / DC / RST / CS | 9 / 8 / 5 / 3 / 4 |
| PCA9685 | SDA / SCL | 1 / 2 |
| 音频 I2S1 | BCLK / WS | **6 / 12**（原 4 / 5） |
| 音频 I2S1 | 麦克风 SD / PCM5102 DIN | 7 / 10（未改） |
| 音频 I2S1 | MCLK | **21**（原 9） |
| 原生 USB | D− / D+ | 19 / 20 |
| UART0 调试 | TX / RX | 43 / 44 |

两颗麦克风共用 SD，L/R 分别接 GND 和 3.3 V。BCLK、WS 改脚要同时改到两颗麦克风与 DAC；MCLK 改到 PCM5102。先核对目标板引脚引出与接线，再烧录。

## 一个 USB：音频＋控制

原生 USB 由 `walle_audio` 的 TinyUSB 统一管理，提供 USB 麦克风、USB 扬声器和一个 CDC 虚拟串口。没有并行启动 Arduino HWCDC/USB 栈。

CDC 由显示项目唯一的命令解析器消费，兼容原来的换行分包、250 ms 空闲提交及 512 字节命令；超过 512 字节的整条命令丢弃。发送端在互斥锁内完整入队一行，避免并发写乱、背压超时留下半行。

原有控制协议继续使用：`getname:WHO_ARE_YOU` 回复 `IAM:WALL_E_TFT`；其余聊天、眼睛、PCA9685、NETCFG v2 及预览协议见 `docs/display`。USB 音频设备名称保持 `Walle UAC Mic`。

**上位机兼容性：**只有一个控制 COM 口；原来查找独立 `IAM:ESP_MIC` 串口的逻辑需要移除或改用该控制口。通过 UAC 选择音频设备的方式保持不变。

网络凭据由上位机经 NETCFG 临时下发，遵循显示项目原有的会话配置方式，不内置 Wi-Fi 密钥。

## 框架与目录

- ESP-IDF 5.5.4＋Arduino-ESP32 3.3.12 组件，CPU 240 MHz。
- `main/`：唯一 `app_main()`，先启动 USB/音频，再启动显示任务。
- `components/walle_audio/`：现有 I2S、USB UAC/CDC、可选 VAD。
- `components/walle_display/src/`：显示应用、网络、舵机及控制通信适配器。
- `components/walle_display/core/`：原 WallEDisplayCore。
- `components/arduino_gfx/`、`jpegdec/`、`animatedgif/`：沿用显示项目的库源码与版本。
- `sdkconfig.defaults`、`dependencies.lock`：可重建的配置与锁定依赖。Arduino 只启用 SPI、Wire、FS、Network、WiFi 库；组件管理器仍会下载其官方清单声明的依赖。
- TinyUSB 固定为 `0.19.0~3`、FFT 固定为 `0.4.0`，沿用官方 ESP-SR `2.4.6`，不依赖来源项目本机的绝对目录。

高优先级音频任务沿用原配置。UI 任务在 Core 1、优先级 1 上运行，每轮至少让出 1 tick；串口/PCA9685 控制与网络任务沿用 Core 0，屏幕仍各用 SPI2/SPI3 DMA。JPEG 缓冲与眼睛画布使用 PSRAM。

## 构建与主机测试

已激活 ESP-IDF 环境时：

```powershell
idf.py build
.\tools\test.ps1
```

本机附带环境助手，默认使用 `D:\Espressif` 中的 ESP-IDF 5.5.4：

```powershell
.\tools\build.ps1 -Target build
.\tools\build.ps1 -Target size
```

主机测试需要 Python、GCC/G++。覆盖真实音频转换、VAD 开关、CDC 原子写入/背压、命令分片与超长边界、显示引脚不变及眼睛渲染。主机测试不能证明硬件音质、帧率、DMA 余量或实际舵机动作。

2026-10-22 已按两个来源的本地最新代码完成核对，补齐显示配网界面并保留音频更新和此前三项控制修复。完整固件构建、`size` 和统一主机测试均通过。应用固件为 `build/walle_esp32.bin`（1,104,288 字节）。静态 DIRAM 占用约 61.0%，实际运行堆余量仍需实测。详细文件变更清单、兼容性及验证结果见 [合并记录](docs/integration.md)。

## 烧录与硬件验证

完成上述音频改线后，确认烧录端口再执行：

```powershell
.\tools\build.ps1 -Target flash -Port COM13
```

COM13 只是示例，不能假设每次相同。通过 CH343/UART 烧录调试，原生 USB 接上位机用于 UAC/CDC；BOOT/RESET 下载方式仍可用。

建议依次验证：单 USB 同时收音和播放；CDC 身份/眼睛/聊天命令；PCA9685；NETCFG 与 JPEG 预览；最后全部同时运行，检查音频断续、控制延迟、帧率、最小堆和任务栈余量。

本次音频主机回归确认了 RX 时钟归属、首包启用 TX、启动失败回滚、写入超时和 PCM 转换。偶发静音的硬件根因与长期稳定性仍未在合并固件实机确认；需验证 USB 枚举前空闲、连续收音时反复开关播放、长时间空闲后恢复播放及 USB 重连。

配网协议边界及成功满 3 秒返回、计时回绕已通过主机测试，实际屏幕显示和整机并发仍需实测。

新固件不会自动替换原项目或推送到原仓库。硬件接线确认前不自动烧录。
