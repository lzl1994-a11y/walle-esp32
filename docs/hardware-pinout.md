# WALL-E 底板引脚与接线表

核对日期：2026-10-22。对应 `E:\walle\walle-esp32` 当前合并代码。

已确认硬件形式：**现成 ESP32-S3 开发板插接到底板；整机独立供电，USB 用于音频和控制数据。** 工程内存配置为 16 MB Flash / 8 MB OPI PSRAM（N16R8）。

已根据用户提供的 **U4、ESP32S3 N16R8、44 脚符号**补充 U4 脚号。GPIO 与 U4 脚号是两套编号；U4 脚号不是 ESP32 模组焊盘号。开发板完整型号和电源原理图尚未提供，排针行间距、封装焊盘编号、安装方向、板载器件占脚与供电隔离仍需按实物核对。

原始符号截图：[U4 引脚符号](hardware-pinout-u4.png)。下表中 TX/RX 按通常的 UART0 TX=GPIO43、RX=GPIO44 解释，需与开发板资料核对。

## 1. 当前固件实际使用的 GPIO

| GPIO | 图中 U4 脚号 | 建议网络名 | 底板连接对象 | 方向（相对 ESP32） |
| --- | --- | --- | --- | --- |
| 1 | 26 | PCA_SDA | PCA9685 SDA | 双向 |
| 2 | 27 | PCA_SCL | PCA9685 SCL | 输出 |
| 3 | 13 | EYE_RST_N | 左、右 GC9A01 的 RST，两屏共用 | 输出；JTAG 绑带脚，见下文 |
| 4 | 4 | EYE_CS_N | 左、右 GC9A01 的 CS，两屏共用 | 输出 |
| 5 | 5 | EYE_DC | 左、右 GC9A01 的 DC，两屏共用 | 输出 |
| 6 | 6 | AUD_BCLK | 两颗 INMP441 的 SCK；PCM5102 的 BCK | 输出 |
| 7 | 7 | MIC_SD | 两颗 INMP441 的 SD 并接 | 输入 |
| 8 | 12 | EYE_MOSI | 左、右 GC9A01 的 DIN/MOSI，两屏共用 | 输出 |
| 9 | 15 | EYE_SCLK | 左、右 GC9A01 的 CLK/SCK，两屏共用 | 输出 |
| 10 | 16 | DAC_DIN | PCM5102 的 DIN | 输出 |
| 11 | 17 | FONT_CS_N | 胸屏配套字库 Flash 的 CS | 输出 |
| 12 | 18 | AUD_LRCK | 两颗 INMP441 的 WS；PCM5102 的 LRCK/LCK | 输出 |
| 13 | 19 | TFT_DC | 胸屏 ST7789 的 DC | 输出 |
| 14 | 20 | TFT_CS_N | 胸屏 ST7789 的 CS | 输出 |
| 15 | 8 | TFT_RST_N | 胸屏 ST7789 的 RST | 输出 |
| 16 | 9 | TFT_MISO | 胸屏配套字库 Flash 的 DO/SDO | 输入 |
| 17 | 10 | TFT_MOSI | 胸屏 ST7789 的 DIN；字库 Flash 的 DI，共用总线 | 输出 |
| 18 | 11 | TFT_SCLK | 胸屏 ST7789 的 CLK；字库 Flash 的 CLK，共用总线 | 输出 |
| 19 | 42 | USB_DM | 原生 USB D− | USB 专用 |
| 20 | 41 | USB_DP | 原生 USB D+ | USB 专用 |
| 21 | 40 | AUD_MCLK | PCM5102 的 SCK/MCLK（系统主时钟） | 输出 |
| 43 | 24（TX） | UART0_TX | 调试/烧录接口 RX | 输出 |
| 44 | 25（RX） | UART0_RX | 调试/烧录接口 TX | 输入 |

当前 GPIO1～21 均有用途。显示项目引脚未变；相对原音频项目，仅 BCLK：4→6、WS：5→12、MCLK：9→21。

代码依据：

- 显示、字库、PCA9685：`components/walle_display/src/config/Config.h`。
- 音频：`components/walle_audio/i2s_mic_driver.c`。
- USB 描述符和驱动：`components/walle_audio/usb_composite.c`；原生 USB 固定使用 GPIO19/20。

## 2. 两颗麦克风与 DAC

| 信号 | Mic0（左时隙） | Mic1（右时隙） | PCM5102 |
| --- | --- | --- | --- |
| BCLK | SCK → GPIO6 | SCK → GPIO6 | BCK → GPIO6 |
| WS/LRCK | WS → GPIO12 | WS → GPIO12 | LRCK/LCK → GPIO12 |
| 采集数据 | SD → GPIO7 | SD → GPIO7 | — |
| 播放数据 | — | — | DIN → GPIO10 |
| 系统主时钟 | 不需要 | 不需要 | SCK/MCLK → GPIO21 |
| L/R 选择 | GND | 3.3 V | — |
| 地 | GND | GND | GND |

- INMP441 使用 3.3 V 供电，各麦克风附近放置去耦电容；共用 SD 线按数据手册预留 100 kΩ 下拉，模块已有时核对是否需要重复安装。[INMP441 数据手册](https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf)
- “左/右时隙”仅表示 I2S 声道，不代表机器人实体左右位置。当前 USB 只上传 Mic0，固件内部仍采集两路；定位已删除，VAD 停用。
- 当前时钟为 LRCK 48 kHz、BCLK 3.072 MHz、MCLK 12.288 MHz。I2S 使用 Philips 格式、双声道、每时隙 32 bit。
- **PCM5102 的 BCK 与 SCK 不是同一个信号**：BCK 接 GPIO6，SCK/MCLK 接 GPIO21。部分现成 DAC 模块把 SCK 接地以使用内部 PLL；若使用这种模块，先核对/断开该接地配置，不能把 GPIO21 直接接到接地的 SCK。
- DAC 设置为 I2S 格式（FMT 低），正常播放时 XSMT 为高。OUTL/OUTR 是线路输出，接功放输入；供电和外围元件按实际 DAC 模块或芯片参考设计连接。[TI PCM5102A 数据手册](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf)

## 3. 屏幕、字库与舵机

- 两块眼屏的 CLK、DIN、DC、RST、CS 全部共用，因此当前两眼显示同一画面。若要独立画面，需要另外分配片选并改代码。
- 眼屏常把 SPI 的 DIN 标为 SDA、CLK 标为 SCL；它们仍是 SPI 信号，不接 PCA9685 的 I2C。
- 胸屏字库功能已启用，因此 GPIO11、16 必须保留。若重新放置裸 Flash，需要匹配现有字库数据，空白 Flash 不能直接显示中文字库。
- 当前没有背光 PWM GPIO；屏幕的 BL/LED 按实际屏幕模块的供电与背光驱动要求连接，不能默认是可直接接 ESP32 的逻辑输入。
- PCA9685 使用地址 0x40、I2C 400 kHz、舵机 PWM 50 Hz。地址脚配置为 A0～A5 低电平；逻辑 VCC 和 I2C 上拉使用 3.3 V，舵机 V+ 使用独立、容量合适的舵机电源，所有接口共地。上拉阻值按总线电容核算，先核对模块已有上拉。
- 当前固件没有控制 PCA9685 的 OE；沿用常见模块的低电平使能方式，并核对实际模块。当前未分配电池电压 ADC 引脚。

## 4. 独立供电与原生 USB

原生 USB 一个口同时承载 UAC 麦克风、UAC 扬声器和 CDC 控制。UART0 用于调试/烧录，业务命令走原生 USB CDC。

### USB VBUS 检测预留

**建议底板预留 GPIO38（图中 U4-32）→ USB_VBUS_DET，但它只是新增硬件预留，当前固件尚未使用。** 符号已经引出 GPIO38，仍需确认实板未被板载器件占用。

检测链路为：USB 插座原始 VBUS → 电阻分压或比较器 → GPIO38。检测点应来自 USB 线缆侧，不是始终存在的外部 5 V。5 V VBUS 不能直接进入 ESP32 GPIO。分压/比较器需满足输入电平和拔线响应要求。[乐鑫自供电 USB 说明](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html#self-powered-device)

当前 `usb_composite.c` 的 USB 配置描述符仍声明总线供电、100 mA，PHY 未启用自供电 VBUS 检测。采用本次独立供电方案后，需同时修改自供电描述符、`phy.self_powered` 与 `phy.vbus_monitor_io`；仅在底板连接 GPIO38 不会自动生效。

### 开发板供电路径

- 外部电源通过开发板明确允许的供电入口接入；VIN/5V/3V3 的含义以该开发板原理图为准。不要同时并联两路 3.3 V 稳压器输出。
- USB VBUS 与整机外部电源不能未经核对直接并接。按开发板已有的二极管/电源选择电路决定是否补充防反灌或隔离；“USB 只传数据”不等于 VBUS 可以省略检测。
- 图中 U4-21 是 `5VIN`，U4-1/2 是 `3.3`，U4-22/23/43/44 是 GND。独立电源若稳压为 5 V，需确认开发板允许从 `5VIN` 输入及其与 USB VBUS 的隔离关系后再接；不要将电池原始电压或 5 V 接到 `3.3`。
- 优先使用开发板现有的原生 USB 插座。若底板另外引出原生 USB，需设计成连接路径二选一，避免同时接两台主机及形成长支线；原生 USB 不是板上 USB-UART 桥的那个口。
- 若底板新布 USB 数据线，按 90 Ω 差分阻抗、连续参考地和短走线设计；ESD 和串联电阻需结合开发板已有电路核对，避免重复堆叠。[乐鑫 PCB 指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

## 5. 启动、调试与扩展预留

| 信号 | 连接/处理 |
| --- | --- |
| GPIO0 / BOOT（U4-36） | 保留开发板原有上拉与 BOOT 按键；底板可引出测试点，按下接 GND |
| EN / RESET（U4-3，图中 RST） | 保留开发板原有复位电路；底板可引出测试点/复位按键 |
| GPIO43 / GPIO44 | 保留 UART0 TX/RX，建议底板引出 GND、TX、RX、BOOT、EN 测试接口，使用 3.3 V 逻辑 |
| GPIO38 | 优先预留 USB VBUS 检测，须核对开发板板载占用；当前软件未启用 |
| GPIO39～42、47、48 | 当前应用未分配，可作为扩展候选；须核对板载 RGB LED、JTAG 等实际占用 |
| GPIO35～37 | N16R8 模组被 OPI PSRAM 占用，不能作为普通扩展引脚使用 |
| GPIO45、46 | 绑带脚，底板不分配新外设，保留开发板原有启动电平 |

GPIO3 当前连接双眼 RST，同时属于 JTAG 选择绑带脚。它没有内部上下拉；根据开发板与屏幕已有电路为其提供确定的复位期间电平，可预留上拉与 0 Ω 隔离位置。默认 eFuse 配置下 JTAG 选择忽略 GPIO3，但不能把它当作完全没有启动约束的普通脚。[ESP32-S3-WROOM-1 数据手册，第 4 章](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)

## 6. 画板核对项与验证状态

1. 开发板型号确定后，按实物/原理图确认排针顺序、行间距、板子正反方向和 USB/按键空间；GPIO 编号不能当作排针脚号。
2. 核对开发板 16 MB Flash / 8 MB OPI PSRAM 配置，确认 GPIO1～21、43、44 的可用性及板载占用，检查 GPIO38 检测预留。
3. 按开发板电源原理图落实独立供电、USB VBUS 检测和防反灌。固件自供电适配尚待硬件确认后完成。
4. 舵机/功放电流回路与麦克风、DAC 电源布线分别处理，保持连续地参考；按整机峰值负载确定电源容量。开发板天线区域按厂商要求留空。
5. 胸屏当前 80 MHz、眼屏 40 MHz，SPI 和 I2S 时钟尽量短，避免长排线、过长分叉；时钟源端可预留串联电阻调试位置。

GPIO 配置已按当前代码逐项核对；`python -B tests/test_pin_map.py` 已通过，验证显示引脚不变、音频和原生 USB 无冲突。本文只新增硬件文档，没有改动 GPIO 或 USB 固件，没有烧录。U4 编号已按截图核对；实板封装及电源路径仍待开发板资料核验。

## 附：截图中完整 U4 编号

下表左右对应截图从上到下的两列，不代表 PCB 封装可直接照此自动编号。

| 左列 U4 脚号 | 符号标注 | 右列 U4 脚号 | 符号标注 |
| --- | --- | --- | --- |
| 1 | 3.3 | 23 | GND |
| 2 | 3.3 | 24 | TX |
| 3 | RST | 25 | RX |
| 4 | GPIO4 | 26 | GPIO1 |
| 5 | GPIO5 | 27 | GPIO2 |
| 6 | GPIO6 | 28 | GPIO42 |
| 7 | GPIO7 | 29 | GPIO41 |
| 8 | GPIO15 | 30 | GPIO40 |
| 9 | GPIO16 | 31 | GPIO39 |
| 10 | GPIO17 | 32 | GPIO38 |
| 11 | GPIO18 | 33 | GPIO37（PSRAM 占用） |
| 12 | GPIO8 | 34 | GPIO36（PSRAM 占用） |
| 13 | GPIO3 | 35 | GPIO35（PSRAM 占用） |
| 14 | GPIO46 | 36 | GPIO0 / BOOT |
| 15 | GPIO9 | 37 | GPIO45 |
| 16 | GPIO10 | 38 | GPIO48 |
| 17 | GPIO11 | 39 | GPIO47 |
| 18 | GPIO12 | 40 | GPIO21 |
| 19 | GPIO13 | 41 | GPIO20 / USB D+ |
| 20 | GPIO14 | 42 | GPIO19 / USB D− |
| 21 | 5VIN | 43 | GND |
| 22 | GND | 44 | GND |
