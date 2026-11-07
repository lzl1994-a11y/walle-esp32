"""Protect the inherited display wiring and the remapped audio wiring."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def main():
    source = (ROOT / "components/walle_display/src/config/Config.h").read_text(encoding="utf-8")
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    values = dict((name, int(value)) for name, value in re.findall(
        r"constexpr int (\w+) = (-?\d+);", source))
    expected = {
        "kTftSck":18, "kTftMosi":17, "kTftMiso":16, "kTftDc":13,
        "kTftRst":15, "kTftCs":14, "kScreenFontCs":11,
        "eysTftSck":9, "eysTftMosi":8, "eysTftDc":5, "eysTftRst":3, "eysTftCs":4,
        "kPca9685Sda":1, "kPca9685Scl":2,
    }
    assert all(values.get(k) == v for k,v in expected.items()), "Display wiring changed"
    driver = (ROOT / "components/walle_audio/i2s_mic_driver.c").read_text(encoding="utf-8")
    audio = dict((name, int(value)) for name,value in re.findall(
        r"#define (I2S_\w+_GPIO) GPIO_NUM_(\d+)", driver))
    assert audio == {
        "I2S_BCLK_GPIO":6, "I2S_WS_GPIO":12, "I2S_DIN_GPIO":7,
        "I2S_DOUT_GPIO":10, "I2S_MCLK_GPIO":21,
    }
    used = list(expected.values()) + list(audio.values()) + [19,20]
    assert len(used) == len(set(used)), "Peripheral/USB pin conflict"
    print("PASS: all display/PCA9685 GPIOs unchanged; audio and native USB have no pin conflicts")

if __name__ == "__main__":
    main()
