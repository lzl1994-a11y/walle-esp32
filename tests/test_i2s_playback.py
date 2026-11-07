"""Check I2S clock ownership, lazy TX startup and PCM writes using host sinks.

Run: python tests/test_i2s_playback.py (requires host GCC).
This does not simulate the ESP32 clock or DMA hardware.
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from test_audio_capture import ROOT, function


def main():
    compiler = shutil.which("gcc")
    if compiler is None:
        raise SystemExit("Host GCC is required on PATH")
    source = (ROOT / "components/walle_audio/i2s_mic_driver.c").read_text(encoding="utf-8")
    constants = "\n".join(re.findall(r"^#define I2S_[^\n]+", source, re.M))
    program = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
typedef int esp_err_t;
typedef int BaseType_t;
typedef void *TaskHandle_t;
enum { ESP_OK, ESP_ERR_INVALID_STATE, ESP_ERR_INVALID_ARG, ESP_ERR_INVALID_SIZE,
       ESP_ERR_TIMEOUT, ESP_ERR_NO_MEM };
#define portMAX_DELAY UINT32_MAX
#define pdMS_TO_TICKS(ms) (ms)
#define pdPASS 1
#define I2S_NUM_1 1
#define I2S_ROLE_MASTER 1
#define GPIO_NUM_7 7
#define GPIO_NUM_10 10
#define TAG "test"
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
typedef struct { int dma_desc_num, dma_frame_num; bool auto_clear_after_cb; } i2s_chan_config_t;
typedef struct { int unused; } i2s_std_config_t;
#define I2S_CHANNEL_DEFAULT_CONFIG(port, role) ((i2s_chan_config_t){0})
static bool s_started = true, s_tx_enabled = true;
static void *s_i2s1_tx = (void *)1;
static void *s_i2s1_rx = (void *)2;
static bool s_initialized;
static TaskHandle_t s_capture_task;
static size_t s_samples_per_channel = 4;
static int32_t raw[8], sink[8];
static int32_t *s_tx_raw_buf = raw;
/* Baseline startup used these; keep mock SDK hooks available for old-source checks. */
size_t s_i2s_read_bytes = sizeof(raw);
static size_t sink_bytes;
static bool short_write;
static esp_err_t write_result, enable_result, flush_result, init_result;
static bool task_fails, play_during_task_create;
static unsigned tx_enables, tx_disables, rx_enables, rx_disables, init_count;
static void *first_initialized;
esp_err_t i2s_new_channel(const i2s_chan_config_t *cfg, void **tx, void **rx)
{ (void)cfg; *tx = (void *)1; *rx = (void *)2; return ESP_OK; }
i2s_std_config_t make_std_rx_config(int din, int dout)
{ (void)din; (void)dout; return (i2s_std_config_t){0}; }
esp_err_t i2s_channel_init_std_mode(void *handle, const i2s_std_config_t *cfg)
{ (void)cfg; if (init_count++ == 0) first_initialized = handle; return init_result; }
esp_err_t i2s_channel_enable(void *handle)
{
    if (handle == s_i2s1_tx) tx_enables++; else { assert(handle == s_i2s1_rx); rx_enables++; }
    return enable_result;
}
esp_err_t i2s_channel_disable(void *handle)
{ if (handle == s_i2s1_rx) rx_disables++; else tx_disables++; return ESP_OK; }
esp_err_t i2s_channel_preload_data(void *h, const void *p, size_t n, size_t *loaded)
{ (void)h; (void)p; *loaded = n; return ESP_OK; }
esp_err_t flush_startup_frames(void) { return flush_result; }
void vTaskDelay(unsigned ticks) { (void)ticks; }
void i2s_capture_task(void *arg) { (void)arg; }
esp_err_t i2s_mic_driver_write_tx(const int16_t *pcm_stereo, size_t num_samples);
BaseType_t xTaskCreatePinnedToCore(void (*entry)(void *), const char *name,
                                 unsigned stack, void *arg, unsigned priority,
                                 TaskHandle_t *handle, unsigned core)
{
    (void)entry; (void)name; (void)stack; (void)arg; (void)priority; (void)core;
    if (play_during_task_create) {
        const int16_t packet[2] = {1, -1};
        assert(i2s_mic_driver_write_tx(packet, 1) == ESP_OK);
    }
    *handle = NULL; return task_fails ? 0 : pdPASS;
}
static esp_err_t i2s_channel_write(void *handle, const void *src, size_t size,
                                  size_t *written, uint32_t timeout)
{
    assert(handle == s_i2s1_tx && timeout > 0 && timeout <= 200);
    assert(size <= sizeof(sink));
    sink_bytes = size;
    memcpy(sink, src, size);
    *written = short_write ? size / 2 : size;
    return write_result;
}
""" + constants + "\n" + "\n".join(function(source, name) for name in (
        "init_i2s_channel", "i2s_mic_driver_start", "i2s_mic_driver_write_tx",
    )) + r"""
int main(void)
{
    assert(init_i2s_channel() == ESP_OK);
    assert(init_count == 2 && first_initialized == s_i2s1_rx);
    init_result = ESP_ERR_NO_MEM;
    assert(init_i2s_channel() == ESP_ERR_NO_MEM);
    init_result = ESP_OK;
    s_started = false; s_tx_enabled = false;
    assert(i2s_mic_driver_start() == ESP_ERR_INVALID_STATE);
    s_initialized = true;
    enable_result = ESP_ERR_INVALID_STATE;
    assert(i2s_mic_driver_start() == ESP_ERR_INVALID_STATE && !s_started);
    enable_result = ESP_OK;
    flush_result = ESP_ERR_TIMEOUT;
    assert(i2s_mic_driver_start() == ESP_ERR_TIMEOUT && !s_started);
    assert(rx_disables == 1 && tx_enables == 0);
    flush_result = ESP_OK; task_fails = true;
    assert(i2s_mic_driver_start() == ESP_ERR_NO_MEM && !s_started);
    assert(rx_disables == 2 && tx_enables == 0);
    task_fails = false;
    assert(i2s_mic_driver_start() == ESP_OK && s_started);
    assert(rx_enables == 4 && !s_tx_enabled && tx_enables == 0);
    assert(i2s_mic_driver_start() == ESP_ERR_INVALID_STATE);
    int16_t pcm[] = {32767, -32768, 1, -1, 0, 0, 8191, -8192};
    const int32_t expected[] = {
        2147418112, INT32_MIN, 262144, -262144, 0, 0, 2147221504, INT32_MIN
    };
    assert(i2s_mic_driver_write_tx(NULL, 1) == ESP_ERR_INVALID_ARG);
    assert(i2s_mic_driver_write_tx(pcm, 0) == ESP_ERR_INVALID_ARG);
    assert(i2s_mic_driver_write_tx(pcm, 5) == ESP_ERR_INVALID_SIZE);
    assert(tx_enables == 0);
    enable_result = ESP_ERR_INVALID_STATE;
    assert(i2s_mic_driver_write_tx(pcm, 4) == ESP_ERR_INVALID_STATE);
    assert(!s_tx_enabled && sink_bytes == 0);
    enable_result = ESP_OK;
    assert(i2s_mic_driver_write_tx(pcm, 4) == ESP_OK && s_tx_enabled);
    assert(tx_enables == 2);
    assert(sink_bytes == sizeof(expected));
    assert(memcmp(sink, expected, sizeof(expected)) == 0);
    assert(i2s_mic_driver_write_tx(pcm + 2, 1) == ESP_OK);
    assert(tx_enables == 2);
    assert(sink_bytes == 8 && sink[0] == 262144 && sink[1] == -262144);
    assert(i2s_mic_driver_write_tx(NULL, 1) == ESP_ERR_INVALID_ARG);
    assert(i2s_mic_driver_write_tx(pcm, 0) == ESP_ERR_INVALID_ARG);
    assert(i2s_mic_driver_write_tx(pcm, 5) == ESP_ERR_INVALID_SIZE);
    short_write = true;
    assert(i2s_mic_driver_write_tx(pcm, 1) == ESP_ERR_INVALID_SIZE);
    short_write = false;
    write_result = ESP_ERR_TIMEOUT;
    assert(i2s_mic_driver_write_tx(pcm, 1) == ESP_ERR_TIMEOUT);
    s_started = false;
    assert(i2s_mic_driver_write_tx(pcm, 1) == ESP_ERR_INVALID_STATE);
    s_tx_enabled = false; write_result = ESP_OK;
    task_fails = true; play_during_task_create = true;
    assert(i2s_mic_driver_start() == ESP_ERR_NO_MEM);
    assert(!s_started && !s_tx_enabled && tx_disables == 1 && rx_disables == 3);
    puts("PASS: RX clock ownership, capture-only startup, lazy TX, startup failures, bounded writes, PCM conversion and errors");
}
"""
    with tempfile.TemporaryDirectory(prefix="i2s-playback-test-") as directory:
        test_source = Path(directory) / "playback_test.c"
        executable = Path(directory) / "playback_test.exe"
        test_source.write_text(program, encoding="utf-8")
        subprocess.run([
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
            str(test_source), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
