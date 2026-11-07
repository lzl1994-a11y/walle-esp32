"""Compile the production CDC transport against a bounded host USB FIFO."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from test_audio_capture import ROOT, function

def main():
    compiler = shutil.which("gcc")
    if not compiler:
        raise SystemExit("Host GCC is required")
    source = (ROOT / "components/walle_audio/usb_composite.c").read_text(encoding="utf-8")
    config = (ROOT / "components/walle_audio/tusb_config.h").read_text(encoding="utf-8")
    capacity = re.search(r"^#define CFG_TUD_CDC_TX_BUFSIZE .+$", config, re.M).group()
    prelude = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
typedef int esp_err_t;
typedef uint32_t TickType_t;
enum { ESP_OK, ESP_ERR_INVALID_ARG, ESP_ERR_INVALID_SIZE, ESP_ERR_INVALID_STATE,
       ESP_ERR_TIMEOUT, ESP_FAIL };
#define portMAX_DELAY UINT32_MAX
#define pdMS_TO_TICKS(ms) (ms)
static bool mounted = true, release_space;
static uint32_t tick, waited, flushes, writes, space;
static size_t sent_length, rx_offset;
static uint8_t sent[4096], rx[] = {1,2,3,4,5};
static bool tud_mounted(void) { return mounted; }
static uint32_t xTaskGetTickCount(void) { return tick; }
static void vTaskDelay(TickType_t ms) {
    tick += ms; waited += ms;
    if (release_space && waited >= 3) space = 2048;
}
static uint32_t tud_cdc_n_available(int port) {
    assert(port == 0); return sizeof(rx) - rx_offset;
}
static uint32_t tud_cdc_n_read(int port, void *data, uint32_t length) {
    assert(port == 0);
    if (length > sizeof(rx) - rx_offset) length = sizeof(rx) - rx_offset;
    memcpy(data, rx + rx_offset, length); rx_offset += length; return length;
}
static uint32_t tud_cdc_n_write_available(int port) { assert(port == 0); return space; }
static uint32_t tud_cdc_n_write(int port, const void *data, uint32_t length) {
    assert(port == 0 && length <= space && length <= sizeof(sent));
    memcpy(sent, data, length); sent_length = length; ++writes;
    space -= length; return length;
}
static uint32_t tud_cdc_n_write_flush(int port) { assert(port == 0); return ++flushes; }
"""
    assertions = r"""
int main(void) {
    uint8_t data[514], received[5];
    memset(data, 'x', sizeof(data)); data[512]='\r'; data[513]='\n';
    assert(CFG_TUD_CDC_TX_BUFSIZE >= sizeof(data));
    space = CFG_TUD_CDC_TX_BUFSIZE;
    assert(usb_composite_cdc_write(data, sizeof(data), 100) == ESP_OK);
    assert(writes == 1 && sent_length == 514 && memcmp(sent, data, 514) == 0);
    assert(usb_composite_cdc_write(NULL, 1, 0) == ESP_ERR_INVALID_ARG);
    assert(usb_composite_cdc_write(data, 0, 0) == ESP_ERR_INVALID_ARG);
    assert(usb_composite_cdc_write(data, CFG_TUD_CDC_TX_BUFSIZE + 1, 0) == ESP_ERR_INVALID_SIZE);
    writes=waited=0; space=10;
    assert(usb_composite_cdc_write(data, sizeof(data), 0) == ESP_ERR_TIMEOUT);
    assert(writes == 0 && waited == 0);
    assert(usb_composite_cdc_write(data, sizeof(data), 5) == ESP_ERR_TIMEOUT);
    assert(writes == 0 && waited == 5);
    waited=0; tick=UINT32_MAX-1;
    assert(usb_composite_cdc_write(data, sizeof(data), 5) == ESP_ERR_TIMEOUT);
    assert(writes == 0 && waited == 5);
    waited=0; release_space=true;
    assert(usb_composite_cdc_write(data, sizeof(data), 100) == ESP_OK);
    assert(writes == 1 && waited == 3);
    assert(usb_composite_cdc_read_available() == 5);
    assert(usb_composite_cdc_read(received, 2) == 2 && received[1] == 2);
    assert(usb_composite_cdc_read(received+2, 3) == 3 && received[4] == 5);
    assert(usb_composite_cdc_read_available() == 0);
    mounted=false;
    assert(usb_composite_cdc_write(data, sizeof(data), 100) == ESP_ERR_INVALID_STATE);
    assert(usb_composite_cdc_read_available() == 0);
    assert(usb_composite_cdc_read(received, 1) == 0);
    puts("PASS: atomic 514-byte CDC writes, backpressure, timeout/wrap and byte reads");
}
"""
    names = ("usb_composite_cdc_read_available", "usb_composite_cdc_read", "usb_composite_cdc_write")
    program = prelude + "\n" + capacity + "\n" + "\n".join(function(source, n) for n in names) + assertions
    with tempfile.TemporaryDirectory(prefix="walle-cdc-") as folder:
        src = Path(folder) / "cdc.c"
        exe = Path(folder) / "cdc.exe"
        src.write_text(program, encoding="utf-8")
        subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)

if __name__ == "__main__":
    main()
