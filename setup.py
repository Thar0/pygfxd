#!/usr/bin/env python3

#  copied from https://stackoverflow.com/questions/4529555/building-a-ctypes-based-c-library-with-distutils
from setuptools import setup, Extension
from distutils.command.build_ext import build_ext as build_ext_orig


class CTypesExtension(Extension):
    pass


class build_ext(build_ext_orig):
    def build_extension(self, ext):
        self._ctypes = isinstance(ext, CTypesExtension)
        if self.compiler.compiler_type is "msvc":
            for e in self.extensions:
                e.extra_compile_args=["/std:c11"]
        return super().build_extension(ext)

    def get_export_symbols(self, ext):
        if self._ctypes:
            return ext.export_symbols
        return super().get_export_symbols(ext)

    def get_ext_filename(self, ext_name):
        if self._ctypes:
            return ext_name + '.so'
        return super().get_ext_filename(ext_name)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pygfxd",
    version="1.0.1",
    author="Tharo",
    description="Python bindings for libgfxd",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules = ["pygfxd"],
    ext_modules=[
        CTypesExtension(
            "libgfxd",
            [
                "libgfxd/gfxd.c",
                "libgfxd/uc_f3d.c",
                "libgfxd/uc_f3db.c",
                "libgfxd/uc_f3dex.c",
                "libgfxd/uc_f3dex2.c",
                "libgfxd/uc_f3dexb.c",
                "libgfxd/uc.c",
            ],
            include_dirs=["libgfxd"]
        ),
    ],
    cmdclass={'build_ext': build_ext},
)
