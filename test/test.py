#!/usr/bin/env python3

from pathlib import Path
from dataclasses import dataclass


DIR = Path(__file__).parent


@dataclass
class Sym:
    name: str
    offset: int
    size: int


def parse_syms(txt: str):
    # parse `nm -format sysv` output

    lines = txt.splitlines()
    lines = [line.strip() for line in lines if line.strip() != ""]

    assert lines[0].startswith("Symbols from"), lines[0]
    lines.pop(0)

    columns_headers = "Name Value Class Type Size Line Section".split()

    assert lines[0].split() == columns_headers, lines[0]
    lines.pop(0)

    syms: list[Sym] = []

    for line in lines:
        parts = line.split("|")
        assert len(parts) == len(columns_headers), parts

        parts = [part.strip() for part in parts]

        name = parts[0]
        offset = parts[1]
        size = parts[4]
        section = parts[6]

        assert section == ".data", parts

        syms.append(Sym(name, int(offset, 16), int(size, 16)))

    syms.sort(key=lambda sym: sym.offset)

    return syms


@dataclass
class TestData:
    syms: list[Sym]
    data: memoryview


def setUpModule():
    global TEST_DATA

    stem = "f3dex2"
    syms = parse_syms((DIR / f"{stem}.txt").read_text())
    data = memoryview((DIR / f"{stem}.bin").read_bytes())

    TEST_DATA = TestData(syms, data)


def tearDownModule():
    global TEST_DATA

    del TEST_DATA


import sys

sys.path.insert(0, str(DIR.absolute().parent))

import pygfxd

# Ensure pygfxd being tested is ours
assert Path(pygfxd.__file__).is_relative_to(DIR.absolute().parent), pygfxd.__file__

from pygfxd import *


import unittest

import tempfile


class TestInputOutput(unittest.TestCase):
    """Test gfxd_input_ and gfxd_output_"""

    def setUp(self):
        self.data: list[Sym, memoryview, str] = []
        for sym in TEST_DATA.syms:
            data = bytes(TEST_DATA.data[sym.offset :][: sym.size])
            expected = {
                "emptyDList": "gsSPEndDisplayList()",
                "oneTriDList": "gsSPVertex(0x42042069, 3, 0)gsSP1Triangle(0, 1, 2, 0)gsSPEndDisplayList()",
                "setLights1DList": "gsSPSetLights1(*(Lightsn *)0x09000000)",
            }[sym.name]
            self.data.append((sym, data, expected))

    def test_gfxd_input_buffer(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                gfxd_input_buffer(data)

                outb = bytes(1000)
                outbuf = gfxd_output_buffer(outb, len(outb))

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                gfxd_execute()

                self.assertEqual(expected, gfxd_buffer_to_string(outbuf))

    def test_gfxd_input_fd(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                with tempfile.TemporaryFile() as input_file:
                    input_file.write(data)
                    input_file.seek(0)
                    gfxd_input_fd(input_file)

                    outb = bytes(1000)
                    outbuf = gfxd_output_buffer(outb, len(outb))

                    gfxd_target(gfxd_f3dex2)
                    gfxd_endian(GfxdEndian.big, 4)

                    gfxd_execute()

                    self.assertEqual(expected, gfxd_buffer_to_string(outbuf))

    def test_gfxd_input_callback(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                remaining_data = [data]

                def callback(bufP, count):
                    newdata = remaining_data[0][:count]
                    from ctypes import c_char

                    buftype = c_char * len(newdata)
                    buf = buftype.from_address(bufP)
                    buf[: len(newdata)] = newdata
                    remaining_data[0] = remaining_data[0][len(newdata) :]
                    return len(newdata)

                gfxd_input_callback(callback)

                outb = bytes(1000)
                outbuf = gfxd_output_buffer(outb, len(outb))

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                gfxd_execute()

                self.assertEqual(expected, gfxd_buffer_to_string(outbuf))

    def test_gfxd_output_buffer(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                gfxd_input_buffer(data)

                outb = bytes(1000)
                outbuf = gfxd_output_buffer(outb, len(outb))

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                gfxd_execute()

                self.assertEqual(expected, gfxd_buffer_to_string(outbuf))

    def test_gfxd_output_fd(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                with tempfile.TemporaryFile() as output_file:
                    gfxd_input_buffer(data)

                    gfxd_output_fd(output_file)

                    gfxd_target(gfxd_f3dex2)
                    gfxd_endian(GfxdEndian.big, 4)

                    gfxd_execute()

                    output_file.seek(0)
                    self.assertEqual(expected, output_file.read().decode())

    def test_gfxd_output_callback(self):
        for sym, data, expected in self.data:
            with self.subTest(sym):
                output = io.BytesIO()

                def callback(buf, count):
                    self.assertEqual(count, len(buf))
                    output.write(buf)
                    return count

                gfxd_input_buffer(data)

                gfxd_output_callback(callback)

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                gfxd_execute()

                self.assertEqual(expected, output.getvalue().decode())


class TestArgumentCallback(unittest.TestCase):
    def setUp(self):
        self.data: list[Sym, memoryview] = []
        for sym in TEST_DATA.syms:
            data = bytes(TEST_DATA.data[sym.offset :][: sym.size])
            self.data.append((sym, data))

    def test_gfxd_vtx_callback(self):
        for sym, data in self.data:
            expected = {
                "emptyDList": [],
                "oneTriDList": [(0x42042069, 3)],
                "setLights1DList": [],
            }[sym.name]
            with self.subTest(sym):
                gfxd_input_buffer(data)

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                verts = []

                def callback(vtx, num):
                    verts.append((vtx, num))
                    return 0

                try:
                    gfxd_vtx_callback(callback)

                    gfxd_execute()
                finally:
                    def callback(vtx, num):
                        return 0
                    gfxd_vtx_callback(callback)

                self.assertEqual(verts, expected)


class TestMacroInfo(unittest.TestCase):
    def setUp(self):
        self.data: list[Sym, memoryview] = []
        for sym in TEST_DATA.syms:
            data = bytes(TEST_DATA.data[sym.offset :][: sym.size])
            self.data.append((sym, data))

    def test_gfxd_foreach_pkt(self):
        for sym, data in self.data:
            expected = {
                "emptyDList": ["gsSPEndDisplayList"],
                "oneTriDList": ["gsSPVertex", "gsSP1Triangle", "gsSPEndDisplayList"],
                "setLights1DList": ["gsSPNumLights", "gsSPLight", "gsSPLight"],
            }[sym.name]
            with self.subTest(sym):
                gfxd_input_buffer(data)

                gfxd_target(gfxd_f3dex2)
                gfxd_endian(GfxdEndian.big, 4)

                packets_names = []

                def foreach_pkt_fn():
                    packets_names.append(gfxd_macro_name())
                    return 0

                def macro_fn():
                    gfxd_foreach_pkt(foreach_pkt_fn)
                    return 0

                gfxd_macro_fn(macro_fn)

                gfxd_execute()

                self.assertEqual(packets_names, expected)


class TestMisc(unittest.TestCase):
    def test_generic(self):
        for sym in TEST_DATA.syms:
            with self.subTest(sym):
                test_one(
                    sym.name,
                    TEST_DATA.data[sym.offset :][: sym.size],
                    silent=True,
                )


def test_one(name: str, data, silent=False):
    def macro_fn():
        gfxd_puts("    ")
        gfxd_macro_dflt()
        gfxd_puts(",\n")
        return 0

    all_vertices = set()

    def vtx_callback(seg, count):
        all_vertices.add(seg)
        return 0

    outb = bytes([0] * 4096)
    outb = None

    temp_file = DIR / ".temp.bin"
    temp_file.write_bytes(data)
    with temp_file.open("rb") as input_file:
        gfxd_input_fd(input_file)

        if not silent:
            gfxd_output_fd(sys.stdout)

        if outb:
            outbuf = gfxd_output_buffer(outb, len(outb))

        gfxd_macro_fn(macro_fn)

        gfxd_target(gfxd_f3dex2)
        gfxd_endian(GfxdEndian.big, 4)

        gfxd_vtx_callback(vtx_callback)

        gfxd_puts(f"Gfx {name}[] = " + "{\n")

        gfxd_execute()

    gfxd_puts("};\n")

    if outb:
        if not silent:
            print(gfxd_buffer_to_string(outbuf))

    if not silent:
        print("Found Vtx segments:")
        print([f"D_{seg:08X}" for seg in all_vertices])


if __name__ == "__main__":
    unittest.main()
