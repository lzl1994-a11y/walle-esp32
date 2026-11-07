# 单板合并记录

## 文件变更清单

本目录为新项目；两个来源项目保持原状。

| 文件或目录 | 处理 |
| --- | --- |
| `main/main.cpp` | 新增统一启动入口，启动现有音频与显示应用 |
| 根目录及各组件 `CMakeLists.txt`、`idf_component.yml` | 新增 ESP-IDF + Arduino 组件构建；排除 Arduino 自带 CDC 回调实现 |
| `sdkconfig.defaults`、`dependencies.lock`、`partitions.csv` | 固定框架版本、N16R8 配置和分区 |
| `components/walle_audio/` | 迁移既有音频实现；I2S 仅改 BCLK/WS/MCLK 引脚；CDC 改为共享字节接口 |
| `components/walle_display/src/display_app.cpp`、`display_app.h` | 将原 setup/loop 接入 FreeRTOS 显示任务 |
| `components/walle_display/src/adapters/transport/ControlTransport.*` | 新增显示控制到既有 USB CDC 的适配层 |
| `components/walle_display/src/adapters/input/SerialInputPort.*` | 复用原解析器，切换 CDC 后端，拒绝整条超长输入 |
| `components/walle_display/src/adapters/log/SerialOutput.h`、`SerialLogger.h` | 使用共享 CDC，保留输出互斥，完整行入队并返回发送状态 |
| `components/walle_display/src/app/AppController.cpp` | NETCFG 应答成功入队后再允许应用配置 |
| 显示其余 `src/`、`core/` | 复用原显示、字体、眼睛、网络、舵机及协议实现 |
| `components/arduino_gfx/`、`jpegdec/`、`animatedgif/` | 复用原库；必要兼容补丁见 `THIRD_PARTY.md` |
| `tests/`、`tools/test*.cpp`、`tools/serial_output_test/` | 迁移已有回归并补充共享 CDC、输入边界与引脚检查 |
| `tools/build.ps1`、`tools/test.ps1` | 新增本机环境构建助手及统一主机测试入口 |
| `README.md`、`THIRD_PARTY.md`、`docs/` | 新接线、协议兼容说明、来源和迁移记录；保留显示协议文档 |

## 保留的权威实现

音频转换沿用 `i2s_mic_driver.c` / `afe_processor.c`，UAC 描述符沿用音频项目。显示命令继续由 AppController 处理，网络配置仍由 NetworkConfigStore / WifiImageStreamClient 处理。没有新增第二套命令解析、网络配置或渲染逻辑。

已按字节核对显示 `Config.h`、EyeRenderer、PCA9685 驱动和音频 `afe_processor.c`，均与来源相同。音频引脚和完整接线表见根目录 README。

## 兼容性与待验证项

- 显示工程从 Arduino 2.0.17 迁移到 ESP-IDF 5.5.4 的 Arduino 3.3.12 组件。源码编译与主机回归不能替代 SPI DMA、字库、Wi-Fi、I2C 的实机验证。
- 控制串口统一为一个 TinyUSB CDC，保留 `IAM:WALL_E_TFT`。上位机不再查找独立 `IAM:ESP_MIC` 串口。USB 音频接口和采样格式保持原有实现。
- UAC 与显示控制使用同一个原生 USB。CDC 波特率不决定音频采样率。
- 显示仍沿用原有启动界面和舵机初始化行为；音频三根改线完成后再进行整机联调。
- 未启用 AEC、定位或 VAD；双麦采集保留，UAC 继续输出 Mic0 单声道。
- 需实测音频同时收放、实时眼睛、JPEG 预览及舵机同时运行时的稳定性、控制延迟、堆和栈余量。

## 实际验证（2026-10-18）

- `.\tools\build.ps1`：通过 ESP-IDF 全量编译、链接、分区尺寸检查，生成 `build/walle_esp32.bin`，1,102,032 字节。应用分区 8,192,000 字节，剩余约 87%。
- `.\tools\build.ps1 -Target size`：通过。静态 DIRAM 占用 207,659 / 341,760 字节，链接布局剩余 134,101 字节；这不代表启动全部任务、Wi-Fi 与 DMA 后的空闲堆。
- `.\tools\test.ps1`：全部通过，包含 VAD=0/1 的音频采集回归、播放转换、CDC 完整行发送/背压/超时、引脚冲突、WTFT/NETCFG、输出互斥、命令分片/超长边界和眼睛渲染。
- ELF 符号检查：只有一个 `app_main`，CDC 接收/线路状态回调来自 esp_tinyusb；最终镜像没有链接 Arduino HWCDC/USBCDC 的 `begin` 实现，显示、网络、舵机和眼睛实现已链接。
- 两个源项目已检查 Git 状态：没有修改其受版本控制的文件；显示项目原有未跟踪素材保持原状。
- 尚未烧录或验证硬件运行。音频接线变化和主控框架迁移需要实机联调。

## 审查修复（2026-10-19）

本次文件变更：

| 文件 | 改动 |
| --- | --- |
| `components/walle_display/src/app/AppController.cpp/.h` | 复用现有网络结果队列和 CDC 输出，控制任务与主循环回退共用发送重试逻辑；保留一条待发最终结果，成功入队后清除。PCA9685 解析在累加前检查 int32 范围，拒绝缺少数字的负号，并在完整命令验证通过后才更新整批值 |
| `components/walle_display/src/adapters/input/SerialInputPort.cpp` | 在消费新字节前处理超长输入的空闲超时，避免延迟轮询误丢下一条合法命令 |
| `tests/test_control_regressions.py` | 新增实际控制器函数回归，覆盖发送失败重试、结果顺序与无重复、正负 int32 边界、溢出及非法命令不覆盖有效值 |
| `tools/test_control_input.cpp` | 补充超长输入后无中间轮询、249/250 ms 边界及计时回绕 |
| `tools/test.ps1` | 将控制器回归加入统一测试入口 |
| `README.md`、本文 | 更新修复说明、固件大小与验证记录 |

兼容性：控制协议、引脚和音频路径不变；原有有符号 int32 输入范围保留，溢出和无数字的字段改为整条拒绝。失败重试覆盖 CDC 接口报告发送失败的情况；入队成功不等于上位机已确认收到，不新增应用层确认协议。

实际执行：

- `.\tools\test.ps1`：全部通过，包括新增控制器回归和输入边界，以及原音频、CDC、引脚、图像网络协议和眼睛回归。
- `.\tools\build.ps1`：通过完整固件编译、链接和分区检查，`build/walle_esp32.bin` 为 1,102,144 字节。
- `.\tools\build.ps1 -Target size`：静态 DIRAM 208,171 / 341,760 字节（60.91%），链接布局余量 133,589 字节；运行堆仍需实测。
- 未烧录，未改变两个源项目。

## 按两个本地工作区核对更新（2026-10-22）

来源分析：

- 音频仓库 HEAD 仍为 `5458555`，新增改动尚未提交。已迁入其驱动、测试和依赖约束的工作区更新。来源 `main/i2s_mic_driver.c` 的 SHA256 为 `980005cbfa63fd4378c54e13206c30290372ab3560b2026d42af984e826384ae`。
- 用户最终明确两个来源都以本地代码为准。本轮音频实现已经匹配本地工作区；显示缺少本地新增配网界面，现已补齐。显示当前 HEAD 为 `c494b01`，比对和生成差异使用工作区文件，提交号仅供追溯。
- 显示来源 `src/app/AppController.cpp` SHA256 为 `9f5b4d2c743184f1bf24f0b5c3b6535665cc3b785ff002685c8c14bbe3c8a5c4`；`src/domain/HostNetworkScreen.h` 为 `56f01f7852c6c9f42365b7029bf4634631eae6b1e1f0212836c226c4aa7b8b9b`。
- 音频驱动与来源按文本核对，仅 BCLK/WS/MCLK 的 `4/5/9` 改为合并项目的 `6/12/21`。显示适配器、显示端口和 `Config.h` 与当前本地来源一致，采集处理和通用显示核心按字节核对一致。保留共享 CDC 适配及网络结果发送、超长输入、舵机整数校验三项修复。

文件变更清单：

| 文件 | 同步内容 |
| --- | --- |
| `components/walle_audio/i2s_mic_driver.c` | RX 优先初始化为时钟主通道，采集启动不提前启用 TX；TX 首包启用，写入等待上限 100 ms，保留启动失败回滚 |
| `components/walle_audio/idf_component.yml`、`dependencies.lock` | 明确 TinyUSB `0.19.0~3`、FFT `0.4.0`，保留合并项目 Arduino 与官方 ESP-SR 依赖，不覆盖成来源仓库的本机路径锁文件 |
| `tests/test_i2s_playback.py` | 迁入来源播放回归，仅适配组件路径 |
| `components/walle_display/src/app/AppController.cpp/.h`、`src/adapters/display/St7789DisplayPort.cpp/.h`、`src/ports/IDisplayPort.h` | 补齐本地配网界面及成功 3 秒返回，配网期间保护屏幕不被其他事件覆盖，保留已有三项修复（`src/` 均位于 `components/walle_display/`） |
| `components/walle_display/src/domain/HostNetworkScreen.h` | 迁入本地配网字段解析，并修复嵌入 NUL 提前终止扫描的边界 |
| `tools/test_host_network_screen.cpp`、`tests/test_control_regressions.py`、`tools/test.ps1` | 配网解析回归、NUL 拒绝、未完成状态保持、成功 2999/3000 ms 返回边界和计时回绕，纳入统一测试 |
| `docs/display/host-wifi.md`、`README.md`、`THIRD_PARTY.md`、本文 | 更新共享 CDC 用法、本地来源依据及最终验证结果 |

验证证据：

- 先将来源新增播放测试运行在迁移前的合并驱动上，在“首个初始化通道必须为 RX”断言失败；迁入驱动后通过。
- 对本地配网解析器构造“合法字段＋NUL＋隐藏尾部”，拒绝断言稳定失败。根因是以 C 字符串结束符作为原始包扫描边界；在权威解析函数按实际包长度扫描后通过，正常协议和字段范围不变。
- `.\tools\test.ps1`：全部通过，包括音频启动/PCM/VAD、CDC、三项控制修复、配网字段解析、成功返回计时、引脚一致性、网络协议和眼睛渲染。
- `.\tools\build.ps1`：重新构建通过，`build/walle_esp32.bin` 为 1,104,288 字节。ELF 已确认包含配网显示、成功返回和原网络结果发送修复。
- `.\tools\build.ps1 -Target size`：静态 DIRAM 208,307 / 341,760 字节（60.95%），链接布局余量 133,453 字节；不等于运行后的空闲堆。
- 两个来源仓库的修改状态保持原样；本次未提交、推送或烧录。

实机待验证：偶发静音的硬件根因和修复效果尚未确认。需测试长时间空闲后播放、边收音边开关播放和 USB 重连，以及配网画面、失败提示和成功返回。原 NETCFG v2 和 JPEG 预览保留，新增界面仍通过共享 CDC 控制。
