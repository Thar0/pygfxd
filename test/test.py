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


import sys

sys.path.insert(0, str(DIR.absolute().parent))

import pygfxd

# Ensure pygfxd being tested is ours
assert Path(pygfxd.__file__).is_relative_to(DIR.absolute().parent), pygfxd.__file__

from pygfxd import *


def test_one(name: str, data: memoryview):
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
        print(gfxd_buffer_to_string(outbuf))

    print("Found Vtx segments:")
    print([f"D_{seg:08X}" for seg in all_vertices])


def test(stem: str):
    syms = parse_syms((DIR / f"{stem}.txt").read_text())
    data = memoryview((DIR / f"{stem}.bin").read_bytes())

    for sym in syms:
        print(sym)
        print()
        test_one(sym.name, data[sym.offset :][: sym.size])
        print()


test("f3dex2")
