# -*- coding: utf-8 -*-
import pytest
from Common.utils.helpers import (
    dmx_to_hex, dmx_to_percent, percent_to_dmx,
    universe_address, address_to_universe,
    rgb_to_hex, hex_to_rgb, kelvin_to_rgb,
    format_timecode, safe_filename, ensure_dir,
    load_json, save_json,
)


class TestDmxConversion:
    def test_dmx_to_hex_zero(self):
        assert dmx_to_hex(0) == "0x00"

    def test_dmx_to_hex_max(self):
        assert dmx_to_hex(255) == "0xFF"

    def test_dmx_to_hex_mid(self):
        assert dmx_to_hex(128) == "0x80"

    def test_dmx_to_hex_clamp_high(self):
        assert dmx_to_hex(300) == "0xFF"

    def test_dmx_to_hex_clamp_low(self):
        assert dmx_to_hex(-10) == "0x00"

    def test_dmx_to_percent(self):
        assert dmx_to_percent(255) == 100.0
        assert dmx_to_percent(0) == 0.0
        assert dmx_to_percent(128) == pytest.approx(50.2, abs=0.1)

    def test_percent_to_dmx(self):
        assert percent_to_dmx(100) == 255
        assert percent_to_dmx(0) == 0
        assert percent_to_dmx(50) == 127


class TestAddressConversion:
    def test_universe_address(self):
        assert universe_address(0, 1) == 1
        assert universe_address(1, 1) == 513

    def test_address_to_universe(self):
        assert address_to_universe(1) == (0, 1)
        assert address_to_universe(513) == (1, 1)
        assert address_to_universe(512) == (0, 512)


class TestColorConversion:
    def test_rgb_to_hex(self):
        assert rgb_to_hex(255, 0, 0) == "#FF0000"
        assert rgb_to_hex(0, 255, 0) == "#00FF00"
        assert rgb_to_hex(0, 0, 255) == "#0000FF"

    def test_rgb_to_hex_clamp(self):
        assert rgb_to_hex(300, -10, 128) == "#FF0080"

    def test_hex_to_rgb(self):
        assert hex_to_rgb("#FF0000") == (255, 0, 0)
        assert hex_to_rgb("#00FF00") == (0, 255, 0)

    def test_hex_to_rgb_short(self):
        assert hex_to_rgb("#F00") == (255, 0, 0)

    def test_kelvin_to_rgb_daylight(self):
        r, g, b = kelvin_to_rgb(6500)
        assert 200 <= r <= 255
        assert 200 <= g <= 255
        assert 200 <= b <= 255

    def test_kelvin_to_rgb_warm(self):
        r, g, b = kelvin_to_rgb(2700)
        assert r > g > b


class TestFormatTimecode:
    def test_basic(self):
        assert format_timecode(1, 2, 3, 4) == "01:02:03:04"

    def test_zeros(self):
        assert format_timecode(0, 0, 0, 0) == "00:00:00:00"


class TestSafeFilename:
    def test_clean_name(self):
        assert safe_filename("hello") == "hello"

    def test_invalid_chars(self):
        result = safe_filename('a<b>c:d"e/f\\g|h?i*j')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_strips_whitespace(self):
        assert safe_filename("  hello  ") == "hello"


class TestFileIO:
    def test_save_and_load_json(self, tmp_path):
        path = tmp_path / "test.json"
        data = {"key": "value", "num": 42}
        save_json(path, data)
        loaded = load_json(path)
        assert loaded == data

    def test_ensure_dir(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        ensure_dir(nested)
        assert nested.exists()
