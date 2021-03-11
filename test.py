#!/usr/bin/env python3
#
#   Test file for pygfxd, test.bin should be valid F3DEX2 gbi commands
#

from pygfxd import *

if __name__ == '__main__':

    def macro_fn():
        gfxd_puts("    ")
        gfxd_macro_dflt()
        gfxd_puts(",\n")
        return 0

    all_vertices = set()

    def vtx_callback(seg, count):
        gfxd_printf(f"D_{seg:08X}")
        all_vertices.add(seg)
        return 1

    input_file = open("test.bin","rb")
    gfxd_input_fd(input_file)

    gfxd_output_fd(sys.stdout)

    gfxd_macro_fn(macro_fn)

    gfxd_target(gfxd_f3dex2)
    gfxd_endian(gfxd_endian_big, 4)

    gfxd_vtx_callback(vtx_callback)

    gfxd_puts("Gfx %s[] = {\n" % "ok")

    gfxd_execute()

    gfxd_puts("};\n")

    print("Found Vtx segments:")
    print([f'D_{seg:08X}' for seg in all_vertices])
