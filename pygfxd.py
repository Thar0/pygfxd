#!/usr/bin/env python3
#
#   Python bindings for libgfxd
#   https://github.com/glankk/libgfxd/
#

import io, os, struct, sys
from ctypes import *
from typing import Callable, Tuple

# ====================================================================
#   Library Internals
# ====================================================================

# target types
class gfx_ucode(Structure):
    _fields_=[("disas_fn",  CFUNCTYPE(c_voidp, c_int32, c_int32)),
              ("combine_fn", CFUNCTYPE(c_voidp, c_int)),
              ("arg_tbl",   c_voidp),
              ("macro_tbl", c_voidp)]

gfx_ucode_t = POINTER(gfx_ucode)

# argument errors
class GfxdArgumentError(Exception):
    """Exception raised for errors in gfxd function arguments.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

# gross way to prevent garbage collection of wrapped callbacks and buffers
__gfxd_buffers_callbacks = {}

def free_buffers_callbacks():
    __gfxd_buffers_callbacks.clear()

# Load the shared library into ctypes
lgfxd = CDLL(os.path.dirname(os.path.realpath(__file__)) + os.sep + "libgfxd.so")

# ====================================================================
#   Constants
# ====================================================================

# target ucodes, loaded from dynamic library
gfxd_f3db   = gfx_ucode_t.in_dll(lgfxd, "gfxd_f3db")
gfxd_f3d    = gfx_ucode_t.in_dll(lgfxd, "gfxd_f3d")
gfxd_f3dexb = gfx_ucode_t.in_dll(lgfxd, "gfxd_f3dexb")
gfxd_f3dex  = gfx_ucode_t.in_dll(lgfxd, "gfxd_f3dex")
gfxd_f3dex2 = gfx_ucode_t.in_dll(lgfxd, "gfxd_f3dex2")

# endian
gfxd_endian_big = 0
gfxd_endian_little = 1
gfxd_endian_host = 2

# cap
gfxd_stop_on_invalid = 0
gfxd_stop_on_end = 1
gfxd_emit_dec_color = 2
gfxd_emit_q_macro = 3
gfxd_emit_ext_macro = 4

# arg format
gfxd_argfmt_i = 0
gfxd_argfmt_u = 1
gfxd_argfmt_f = 2

# macro ids
gfxd_Invalid = 0
gfxd_DPFillRectangle = 1
gfxd_DPFullSync = 2
gfxd_DPLoadSync = 3
gfxd_DPTileSync = 4
gfxd_DPPipeSync = 5
gfxd_DPLoadTLUT_pal16 = 6
gfxd_DPLoadTLUT_pal256 = 7
gfxd_DPLoadMultiBlockYuvS = 8
gfxd_DPLoadMultiBlockYuv = 9
gfxd_DPLoadMultiBlock_4bS = 10
gfxd_DPLoadMultiBlock_4b = 11
gfxd_DPLoadMultiBlockS = 12
gfxd_DPLoadMultiBlock = 13
gfxd__DPLoadTextureBlockYuvS = 14
gfxd__DPLoadTextureBlockYuv = 15
gfxd__DPLoadTextureBlock_4bS = 16
gfxd__DPLoadTextureBlock_4b = 17
gfxd__DPLoadTextureBlockS = 18
gfxd__DPLoadTextureBlock = 19
gfxd_DPLoadTextureBlockYuvS = 20
gfxd_DPLoadTextureBlockYuv = 21
gfxd_DPLoadTextureBlock_4bS = 22
gfxd_DPLoadTextureBlock_4b = 23
gfxd_DPLoadTextureBlockS = 24
gfxd_DPLoadTextureBlock = 25
gfxd_DPLoadMultiTileYuv = 26
gfxd_DPLoadMultiTile_4b = 27
gfxd_DPLoadMultiTile = 28
gfxd__DPLoadTextureTileYuv = 29
gfxd__DPLoadTextureTile_4b = 30
gfxd__DPLoadTextureTile = 31
gfxd_DPLoadTextureTileYuv = 32
gfxd_DPLoadTextureTile_4b = 33
gfxd_DPLoadTextureTile = 34
gfxd_DPLoadBlock = 35
gfxd_DPNoOp = 36
gfxd_DPNoOpTag = 37
gfxd_DPPipelineMode = 38
gfxd_DPSetBlendColor = 39
gfxd_DPSetEnvColor = 40
gfxd_DPSetFillColor = 41
gfxd_DPSetFogColor = 42
gfxd_DPSetPrimColor = 43
gfxd_DPSetColorImage = 44
gfxd_DPSetDepthImage = 45
gfxd_DPSetTextureImage = 46
gfxd_DPSetAlphaCompare = 47
gfxd_DPSetAlphaDither = 48
gfxd_DPSetColorDither = 49
gfxd_DPSetCombineMode = 50
gfxd_DPSetCombineLERP = 51
gfxd_DPSetConvert = 52
gfxd_DPSetTextureConvert = 53
gfxd_DPSetCycleType = 54
gfxd_DPSetDepthSource = 55
gfxd_DPSetCombineKey = 56
gfxd_DPSetKeyGB = 57
gfxd_DPSetKeyR = 58
gfxd_DPSetPrimDepth = 59
gfxd_DPSetRenderMode = 60
gfxd_DPSetScissor = 61
gfxd_DPSetScissorFrac = 62
gfxd_DPSetTextureDetail = 63
gfxd_DPSetTextureFilter = 64
gfxd_DPSetTextureLOD = 65
gfxd_DPSetTextureLUT = 66
gfxd_DPSetTexturePersp = 67
gfxd_DPSetTile = 68
gfxd_DPSetTileSize = 69
gfxd_SP1Triangle = 70
gfxd_SP2Triangles = 71
gfxd_SP1Quadrangle = 72
gfxd_SPBranchLessZ = 73
gfxd_SPBranchLessZrg = 74
gfxd_SPBranchList = 75
gfxd_SPClipRatio = 76
gfxd_SPCullDisplayList = 77
gfxd_SPDisplayList = 78
gfxd_SPEndDisplayList = 79
gfxd_SPFogPosition = 80
gfxd_SPForceMatrix = 81
gfxd_SPSetGeometryMode = 82
gfxd_SPClearGeometryMode = 83
gfxd_SPLoadGeometryMode = 84
gfxd_SPInsertMatrix = 85
gfxd_SPLine3D = 86
gfxd_SPLineW3D = 87
gfxd_SPLoadUcode = 88
gfxd_SPLookAtX = 89
gfxd_SPLookAtY = 90
gfxd_SPLookAt = 91
gfxd_SPMatrix = 92
gfxd_SPModifyVertex = 93
gfxd_SPPerspNormalize = 94
gfxd_SPPopMatrix = 95
gfxd_SPPopMatrixN = 96
gfxd_SPSegment = 97
gfxd_SPSetLights1 = 98
gfxd_SPSetLights2 = 99
gfxd_SPSetLights3 = 100
gfxd_SPSetLights4 = 101
gfxd_SPSetLights5 = 102
gfxd_SPSetLights6 = 103
gfxd_SPSetLights7 = 104
gfxd_SPNumLights = 105
gfxd_SPLight = 106
gfxd_SPLightColor = 107
gfxd_SPTexture = 108
gfxd_SPTextureRectangle = 109
gfxd_SPTextureRectangleFlip = 110
gfxd_SPVertex = 111
gfxd_SPViewport = 112
gfxd_DPLoadTLUTCmd = 113
gfxd_DPLoadTLUT = 114
gfxd_BranchZ = 115
gfxd_DisplayList = 116
gfxd_DPHalf1 = 117
gfxd_DPHalf2 = 118
gfxd_DPLoadTile = 119
gfxd_SPGeometryMode = 120
gfxd_SPSetOtherModeLo = 121
gfxd_SPSetOtherModeHi = 122
gfxd_DPSetOtherMode = 123
gfxd_MoveWd = 124
gfxd_MoveMem = 125
gfxd_SPDma_io = 126
gfxd_SPDmaRead = 127
gfxd_SPDmaWrite = 128
gfxd_LoadUcode = 129
gfxd_SPLoadUcodeEx = 130
gfxd_TexRect = 131
gfxd_TexRectFlip = 132
gfxd_SPNoOp = 133
gfxd_Special3 = 134
gfxd_Special2 = 135
gfxd_Special1 = 136

# argument types
gfxd_Word = 0
gfxd_Opcode = 1
gfxd_Coordi = 2
gfxd_Coordq = 3
gfxd_Pal = 4
gfxd_Tlut = 5
gfxd_Timg = 6
gfxd_Tmem = 7
gfxd_Tile = 8
gfxd_Fmt = 9
gfxd_Siz = 10
gfxd_Dim = 11
gfxd_Cm = 12
gfxd_Tm = 13
gfxd_Ts = 14
gfxd_Dxt = 15
gfxd_Tag = 16
gfxd_Pm = 17
gfxd_Colorpart = 18
gfxd_Color = 19
gfxd_Lodfrac = 20
gfxd_Cimg = 21
gfxd_Zimg = 22
gfxd_Ac = 23
gfxd_Ad = 24
gfxd_Cd = 25
gfxd_Ccpre = 26
gfxd_Ccmuxa = 27
gfxd_Ccmuxb = 28
gfxd_Ccmuxc = 29
gfxd_Ccmuxd = 30
gfxd_Acmuxabd = 31
gfxd_Acmuxc = 32
gfxd_Cv = 33
gfxd_Tc = 34
gfxd_Cyc = 35
gfxd_Zs = 36
gfxd_Ck = 37
gfxd_Keyscale = 38
gfxd_Keywidth = 39
gfxd_Zi = 40
gfxd_Rm1 = 41
gfxd_Rm2 = 42
gfxd_Sc = 43
gfxd_Td = 44
gfxd_Tf = 45
gfxd_Tl = 46
gfxd_Tt = 47
gfxd_Tp = 48
gfxd_Line = 49
gfxd_Vtx = 50
gfxd_Vtxflag = 51
gfxd_Dl = 52
gfxd_Zraw = 53
gfxd_Dlflag = 54
gfxd_Cr = 55
gfxd_Num = 56
gfxd_Fogz = 57
gfxd_Fogp = 58
gfxd_Mtxptr = 59
gfxd_Gm = 60
gfxd_Mwo_matrix = 61
gfxd_Linewd = 62
gfxd_Uctext = 63
gfxd_Ucdata = 64
gfxd_Size = 65
gfxd_Lookatptr = 66
gfxd_Mtxparam = 67
gfxd_Mtxstack = 68
gfxd_Mwo_point = 69
gfxd_Wscale = 70
gfxd_Seg = 71
gfxd_Segptr = 72
gfxd_Lightsn = 73
gfxd_Numlights = 74
gfxd_Lightnum = 75
gfxd_Lightptr = 76
gfxd_Tcscale = 77
gfxd_Switch = 78
gfxd_St = 79
gfxd_Stdelta = 80
gfxd_Vtxptr = 81
gfxd_Vpptr = 82
gfxd_Dram = 83
gfxd_Sftlo = 84
gfxd_Othermodelo = 85
gfxd_Sfthi = 86
gfxd_Othermodehi = 87
gfxd_Mw = 88
gfxd_Mwo = 89
gfxd_Mwo_clip = 90
gfxd_Mwo_lightcol = 91
gfxd_Mv = 92
gfxd_Mvo = 93
gfxd_Dmem = 94
gfxd_Dmaflag = 95

# ====================================================================
#   Input/output Methods
# ====================================================================

lgfxd.gfxd_input_buffer.argtypes = [c_void_p, c_int]
lgfxd.gfxd_input_buffer.restype = None
def gfxd_input_buffer(buf: bytes, size: int = -1):
    """
    Read input from the buffer pointed to by buf, of size bytes.
    If size is negative, len(buf) is used instead which is
    default.
    """
    size = len(buf) if size < 0 else size

    buffer = create_string_buffer(buf, size)
    __gfxd_buffers_callbacks.update({100 : buffer})
    lgfxd.gfxd_input_buffer(buffer, c_int(size))
    return buffer

lgfxd.gfxd_output_buffer.argtypes = [c_char_p, c_int]
lgfxd.gfxd_output_buffer.restype = None
def gfxd_output_buffer(buf: bytes, size: int = -1):
    """
    Output to the buffer pointed to by buf, of size bytes.
    If size is negative, len(buf) is used instead which is
    default.
    """
    size = len(buf) if size < 0 else size

    buffer = create_string_buffer(buf, size)
    __gfxd_buffers_callbacks.update({101 : buffer})
    lgfxd.gfxd_output_buffer(buffer, c_int(size))
    return buffer

lgfxd.gfxd_input_fd.argtypes = [c_int]
lgfxd.gfxd_input_fd.restype = None
def gfxd_input_fd(stream: io.IOBase):
    """
    Read input from the provided stream implementing IOBase
    """
    lgfxd.gfxd_input_fd(c_int(stream.fileno()))

lgfxd.gfxd_output_fd.argtypes = [c_int]
lgfxd.gfxd_output_fd.restype = None
def gfxd_output_fd(stream: io.IOBase):
    """
    Output to the provided stream implementing IOBase
    """
    lgfxd.gfxd_output_fd(c_int(stream.fileno()))

lgfxd.gfxd_input_callback.argtypes = [CFUNCTYPE(c_int, c_voidp, c_int)]
lgfxd.gfxd_input_callback.restype = None
def gfxd_input_callback(fn: Callable[[bytes, int], int]):
    """
    Use the provided callback function, fn, compatible with the C function type
        int gfxd_input_fn_t(void *buf, int count)

    fn should copy at most count bytes to/from buf, and return the number of bytes actually copied. 
    The input callback should return 0 to signal end of input.
    """
    cb =  CFUNCTYPE(c_int, c_voidp, c_int)(fn)
    __gfxd_buffers_callbacks.update({102 : cb})
    return lgfxd.gfxd_macro_fn(cb)

lgfxd.gfxd_output_callback.argtypes = [CFUNCTYPE(c_int, c_char_p, c_int)]
lgfxd.gfxd_output_callback.restype = None
def gfxd_output_callback(fn: Callable[[bytes, int], int]):
    """
    Use the provided callback function, fn, compatible with C function type
        int gfxd_output_fn_t(const char *buf, int count)

    fn should copy at most count bytes to/from buf, and return the number of bytes actually copied.
    """
    cb = CFUNCTYPE(c_int, c_char_p, c_int)(fn)
    __gfxd_buffers_callbacks.update({103 : cb})
    return lgfxd.gfxd_macro_fn(cb)

# ====================================================================
#   Handlers
# ====================================================================

lgfxd.gfxd_macro_dflt.argtypes = None
lgfxd.gfxd_macro_dflt.restype = c_int
def gfxd_macro_dflt():
    """
    The default macro handler. Outputs the macro name, dynamic display list 
    pointer if one has been specified, and then each argument in order using 
    the function registered using gfxd_arg_fn (gfxd_arg_dflt by default), 
    and returns zero.

    Because it is designed to be extended, it only outputs the macro text, without 
    any whitespace or punctuation before or after. When this function is used as 
    the sole macro handler, it will output the entire display list on one line 
    without any separation between macros, which is probably not what you want.
    """
    return lgfxd.gfxd_macro_dflt()

lgfxd.gfxd_macro_fn.argtypes = [CFUNCTYPE(c_int)]
lgfxd.gfxd_macro_fn.restype = None
def gfxd_macro_fn(fn: Callable[[], int]):
    """
    Set fn to be the macro handler function, compatible with the C function type
        int gfxd_macro_fn_t(void)

    fn can be None, in which case the handler is reset to the default.
    """
    if fn is None:
        lgfxd.gfxd_macro_fn(None)
        return
    cb = CFUNCTYPE(c_int)(fn)
    __gfxd_buffers_callbacks.update({1000 : cb})
    lgfxd.gfxd_macro_fn(cb)

lgfxd.gfxd_arg_dflt.argtypes = [c_int]
lgfxd.gfxd_arg_dflt.restype = None
def gfxd_arg_dflt(arg_num: int):
    """
    The default argument handler for gfxd_macro_dflt.
    For the argument with index arg_num, calls gfxd_arg_callbacks, and prints
    the argument value if the callback returns zero, or if there is no
    callback for the given argument.
    """
    lgfxd.gfxd_arg_dflt(c_int(arg_num))

lgfxd.gfxd_arg_fn.argtypes = [CFUNCTYPE(c_int)]
lgfxd.gfxd_arg_fn.restype = None
def gfxd_arg_fn(fn: Callable[[], int]):
    """
    Set fn to be the argument handler function, called by gfxd_macro_dflt, for each 
    argument in the current macro, not counting the dynamic display list pointer if 
    one has been specified. fn should be compatible with the C function type
        void gfxd_arg_fn_t(int arg_num)

    fn can be None, in which case the handler is reset to 
    the default. This only affects the output of gfxd_macro_dflt, and has no 
    observable effect if gfxd_macro_dflt is overridden (not extended).
    """
    if fn is None:
        lgfxd.gfxd_arg_fn(None)
        return
    cb = CFUNCTYPE(c_int)(fn)
    __gfxd_buffers_callbacks.update({1001 : cb})
    lgfxd.gfxd_arg_fn(cb)

# ====================================================================
#   Argument Callbacks
# ====================================================================

lgfxd.gfxd_arg_callbacks.argtypes = [c_int]
lgfxd.gfxd_arg_callbacks.restype = c_int
def gfxd_arg_callbacks(arg_num: int):
    """
    Examines the argument with index arg_num and executes the callback function for 
    that argument type, if such a callback is supported and has been registered. 
    This function returns the value that was returned by the callback function. 
    If no callback function has been registered for the argument type, zero is returned.

    Most argument callbacks have some extra parameters containing information that 
    might be relevant to the argument that triggered the callback. The extra information 
    is extracted only from the current macro, as gfxd does not retain any context 
    information from previous or subsequent macros. If any of the extra parameter values 
    is not available in the current macro, the value for that parameter is substituted 
    with -1 for signed parameters, and zero for unsigned parameters.
    """
    return lgfxd.gfxd_arg_callbacks(arg_num)

lgfxd.gfxd_tlut_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32, c_int32)]
lgfxd.gfxd_tlut_callback.restype = None
def gfxd_tlut_callback(fn: Callable[[int, int, int], int]):
    """
    Set the callback function for palette arguments, compatible with the C function type
        int gfxd_tlut_fn_t(uint32_t tlut, int32_t idx, int32_t count)

    The argument type is gfxd_Tlut.

    The palette index is in idx and the number of colors in count.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({0 : cb})
    lgfxd.gfxd_tlut_callback(cb)

lgfxd.gfxd_timg_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32, c_int32, c_int32, c_int32, c_int32)]
lgfxd.gfxd_timg_callback.restype = None
def gfxd_timg_callback(fn: Callable[[int, int, int, int, int, int], int]):
    """
    Set the callback function for texture arguments, compatible with the C function type
        int gfxd_timg_fn_t(uint32_t timg, int32_t fmt, int32_t siz, int32_t width, int32_t height, int32_t pal)

    The argument type is gfxd_Timg.

    The image format is in fmt and siz, the dimensions in width and height, and the
    palette index in pal.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32, c_int32, c_int32, c_int32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({1 : cb})
    lgfxd.gfxd_timg_callback(cb)

lgfxd.gfxd_cimg_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32, c_int32, c_int32)]
lgfxd.gfxd_cimg_callback.restype = None
def gfxd_cimg_callback(fn: Callable[[int, int, int, int], int]):
    """
    Set the callback function for frame buffer arguments, compatible with the C function type
        int gfxd_cimg_fn_t(uint32_t cimg, int32_t fmt, int32_t siz, int32_t width)

    The argument type is gfxd_Cimg.

    The image format is in fmt and siz, and the horizontal resolution in width.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32, c_int32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({2 : cb})
    lgfxd.gfxd_cimg_callback(cb)

lgfxd.gfxd_zimg_callback.argtypes = [CFUNCTYPE(c_int, c_uint32)]
lgfxd.gfxd_zimg_callback.restype = None
def gfxd_zimg_callback(fn: Callable[[int], int]):
    """
    Set the callback function for depth buffer arguments, compatible with the C function type
        int gfxd_zimg_fn_t(uint32_t zimg)

    The argument type is gfxd_Zimg.
    """
    cb = CFUNCTYPE(c_int, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({3 : cb})
    lgfxd.gfxd_zimg_callback(cb)

lgfxd.gfxd_dl_callback.argtypes = [CFUNCTYPE(c_int, c_uint32)]
lgfxd.gfxd_dl_callback.restype = None
def gfxd_dl_callback(fn: Callable[[int], int]):
    """
    Set the callback function for display list arguments, compatible with the C function type
        int gfxd_dl_fn_t(uint32_t dl)

    The argument type is gfxd_Dl.
    """
    cb = CFUNCTYPE(c_int, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({4 : cb})
    lgfxd.gfxd_dl_callback(cb)

lgfxd.gfxd_mtx_callback.argtypes = [CFUNCTYPE(c_int, c_uint32)]
lgfxd.gfxd_mtx_callback.restype = None
def gfxd_mtx_callback(fn: Callable[[int], int]):
    """
    Set the callback function for matrix arguments, compatible with the C function type
        int gfxd_mtx_fn_t(uint32_t mtx)

    The argument type is gfxd_Mtxptr.
    """
    cb = CFUNCTYPE(c_int, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({5 : cb})
    lgfxd.gfxd_mtx_callback(cb)

lgfxd.gfxd_lookat_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32)]
lgfxd.gfxd_lookat_callback.restype = None
def gfxd_lookat_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for lookat array arguments, compatible with the C function type
        int gfxd_lookat_fn_t(uint32_t lookat, int32_t count)

    The argument type is gfxd_Lookatptr.

    The number of lookat structures (1 or 2) is in count.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({6 : cb})
    lgfxd.gfxd_lookat_callback(cb)

lgfxd.gfxd_light_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32)]
lgfxd.gfxd_light_callback.restype = None
def gfxd_light_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for light array arguments.
        int gfxd_light_fn_t(uint32_t light, int32_t count)

    The argument type is gfxd_Lightptr.

    The number of light structures is in count.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({7 : cb})
    lgfxd.gfxd_light_callback(cb)

lgfxd.gfxd_seg_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32)]
lgfxd.gfxd_seg_callback.restype = None
def gfxd_seg_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for segment base arguments, compatible with the C function type
        int gfxd_seg_fn_t(uint32_t seg, int32_t num)

    The argument type is gfxd_Segptr.

    The segment number is in num.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({8 : cb})
    lgfxd.gfxd_seg_callback(cb)

lgfxd.gfxd_vtx_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_int32)]
lgfxd.gfxd_vtx_callback.restype = None
def gfxd_vtx_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for vertex array arguments, compatible with the C function type
        int gfxd_vtx_fn_t(uint32_t vtx, int32_t num)

    The argument type is gfxd_Vtxptr.

    The number of vertex structures is in num.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_int32)(fn)
    __gfxd_buffers_callbacks.update({9 : cb})
    lgfxd.gfxd_vtx_callback(cb)

lgfxd.gfxd_vp_callback.argtypes = [CFUNCTYPE(c_int, c_uint32)]
lgfxd.gfxd_vp_callback.restype = None
def gfxd_vp_callback(fn: Callable[[int], int]):
    """
    Set the callback function for viewport arguments, compatible with the C function type
        int gfxd_vp_fn_t(uint32_t vp)

    The argument type is gfxd_Vp.
    """
    cb = CFUNCTYPE(c_int, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({10 : cb})
    lgfxd.gfxd_vp_callback(cb)

lgfxd.gfxd_uctext_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_uint32)]
lgfxd.gfxd_uctext_callback.restype = None
def gfxd_uctext_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for microcode text arguments, compatible with the C function type
        int gfxd_uctext_fn_t(uint32_t text, uint32_t size)

    The argument type is gfxd_Uctext.

    The size of the text segment is in size.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({11 : cb})
    lgfxd.gfxd_uctext_callback(cb)

lgfxd.gfxd_ucdata_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_uint32)]
lgfxd.gfxd_ucdata_callback.restype = None
def gfxd_ucdata_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for microcode data arguments, compatible with the C function type
        int gfxd_ucdata_fn_t(uint32_t data, uint32_t size)

    The argument type is gfxd_Ucdata.

    The size of the data segment is in size.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({12 : cb})
    lgfxd.gfxd_ucdata_callback(cb)

lgfxd.gfxd_dram_callback.argtypes = [CFUNCTYPE(c_int, c_uint32, c_uint32)]
lgfxd.gfxd_dram_callback.restype = None
def gfxd_dram_callback(fn: Callable[[int, int], int]):
    """
    Set the callback function for generic pointer arguments, compatible with the C function type
        int gfxd_dram_fn_t(uint32_t dram, uint32_t size)

    The argument type is gfxd_Dram.

    The size of the data is in size.
    """
    cb = CFUNCTYPE(c_int, c_uint32, c_uint32)(fn)
    __gfxd_buffers_callbacks.update({13 : cb})
    lgfxd.gfxd_dram_callback(cb)

# ====================================================================
#   General Settings
# ====================================================================

lgfxd.gfxd_target.argtypes = [gfx_ucode_t]
lgfxd.gfxd_target.restype = None
def gfxd_target(target: gfx_ucode_t):
    """
    Select ucode as the target microcode.

    ucode can be
        gfxd_f3d
        gfxd_f3db
        gfxd_f3dex
        gfxd_f3dexb
        gfxd_f3dex2

    The microcode must be selected before gfxd_execute, as no microcode is selected by default.
    """
    lgfxd.gfxd_target(target)

lgfxd.gfxd_endian.argtypes = [c_int, c_int]
lgfxd.gfxd_endian.restype = None
def gfxd_endian(endian: int, wordsize: int):
    """
    Select endian as the endianness of the input, and wordsize as the size of each word in number of bytes. 
    
    endian can be
        gfxd_endian_big
        gfxd_endian_little
        gfxd_endian_host (the endianness of the host machine)
    
    wordsize can be 1, 2, 4, or 8. Big endian is selected by default, with a word size of 4.
    """
    lgfxd.gfxd_endian(c_int(endian), c_int(wordsize))

lgfxd.gfxd_dynamic.argtypes = [c_char_p]
lgfxd.gfxd_dynamic.restype = None
def gfxd_dynamic(arg: str):
    """
    Enable or disable the use of dynamic g macros instead of static gs macros, and select the dynamic display list pointer argument to be used.
    arg will be used by gfxd_macro_dflt as the first argument to dynamic macros.

    If arg is None, dynamic macros are disabled, and gs macros are used.

    Also affects the result of gfxd_macro_name, as it will return either the dynamic or static version of the macro name as selected by this setting.
    """
    if arg is None:
        lgfxd.gfxd_dynamic(None)
        return None
    # we want to keep this string around for a while, so buffer it
    buffer = create_string_buffer(arg.encode("utf-8"), len(arg.encode("utf-8")))
    __gfxd_buffers_callbacks.update({10000 : buffer})
    lgfxd.gfxd_dynamic(buffer)
    return buffer

lgfxd.gfxd_enable.argtypes = [c_int]
lgfxd.gfxd_enable.restype = None
def gfxd_enable(cap: int):
    """
    Enable the feature specified by cap. Can be one of the following;

        gfxd_stop_on_invalid:
                Stop execution when encountering an invalid macro. Enabled by default.
        gfxd_stop_on_end:
                Stop execution when encountering a SPBranchList or SPEndDisplayList. Enabled by default.
        gfxd_emit_dec_color:
                Print color components as decimal instead of hexadecimal. Disabled by default.
        gfxd_emit_q_macro:
                Print fixed-point conversion q macros for fixed-point values. Disabled by default.
        gfxd_emit_ext_macro:
                Emit non-standard macros. Some commands are valid (though possibly meaningless), but have no macros associated with them, 
                such as a standalone G_RDPHALF_1. When this feature is enabled, such a command will produce a non-standard gsDPHalf1
                macro instead of a raw hexadecimal command. Also enables some non-standard multi-packet texture loading macros. Disabled
                by default.
    """
    lgfxd.gfxd_enable(cap)

lgfxd.gfxd_disable.argtypes = [c_int]
lgfxd.gfxd_disable.restype = None
def gfxd_disable(cap: int):
    """
    Disable the feature specified by cap. Can be one of the following;

        gfxd_stop_on_invalid:
                Stop execution when encountering an invalid macro. Enabled by default.
        gfxd_stop_on_end:
                Stop execution when encountering a SPBranchList or SPEndDisplayList. Enabled by default.
        gfxd_emit_dec_color:
                Print color components as decimal instead of hexadecimal. Disabled by default.
        gfxd_emit_q_macro:
                Print fixed-point conversion q macros for fixed-point values. Disabled by default.
        gfxd_emit_ext_macro:
                Emit non-standard macros. Some commands are valid (though possibly meaningless), but have no macros associated with them, 
                such as a standalone G_RDPHALF_1. When this feature is enabled, such a command will produce a non-standard gsDPHalf1
                macro instead of a raw hexadecimal command. Also enables some non-standard multi-packet texture loading macros. Disabled
                by default.
    """
    lgfxd.gfxd_disable(cap)

lgfxd.gfxd_udata_set.argtypes = [c_void_p]
lgfxd.gfxd_udata_set.restype = None
def gfxd_udata_set(p: c_void_p):
    """
    Set a generic pointer that can be used to pass user-defined data in and out of callback functions.
    
    The data should be appropriately wrapped with ctypes by the user. 
    """
    lgfxd.gfxd_udata_set(p)

lgfxd.gfxd_udata_set.argtypes = None
lgfxd.gfxd_udata_set.restype = c_void_p
def gfxd_udata_get():
    """
    Get the generic pointer that can be used to pass user-defined data in and out of callback functions.
    
    The data should be appropriately interpreted with ctypes by the user. 
    """
    return lgfxd.gfxd_udata_get()

# ====================================================================
#   Execution
# ====================================================================

lgfxd.gfxd_udata_set.argtypes = None
lgfxd.gfxd_udata_set.restype = c_int
def gfxd_execute():
    """
    Start executing gfxd with the current settings. For each macro, the macro handler registered with gfxd_macro_fn is called.
    
    Execution ends when the input ends, the macro handler returns non-zero, when an invalid macro is encountered and gfxd_stop_on_invalid is enabled,
    or when SPBranchList or SPEndDisplayList is encountered and gfxd_stop_on_end is enabled.
    If execution ends due to an invalid macro, -1 is returned.
    If execution ends because the macro handler returns non-zero, the return value from the macro handler is returned.
    Otherwise zero is returned.
    """
    return lgfxd.gfxd_execute()

# ====================================================================
#   Macro Information
# ====================================================================

lgfxd.gfxd_macro_offset.argtypes = None
lgfxd.gfxd_macro_offset.restype = c_int
def gfxd_macro_offset():
    """
    Returns the offset in the input data of the current macro.
    The offset starts at zero when gfxd_execute is called.
    """
    return lgfxd.gfxd_macro_offset()

lgfxd.gfxd_macro_packets.argtypes = None
lgfxd.gfxd_macro_packets.restype = c_int
def gfxd_macro_packets():
    """
    Returns the number of Gfx packets within the current macro.
    """
    return lgfxd.gfxd_macro_packets()

lgfxd.gfxd_macro_data.argtypes = None
lgfxd.gfxd_macro_data.restype = c_void_p
def gfxd_macro_data():
    """
    Returns a bytearray object of the input data for the current macro.
    The data is not byte-swapped. The data has a length of 8 * gfxd_macro_packets().
    """
    lgfxd.gfxd_macro_data.restype = POINTER(c_ubyte * (8 * gfxd_macro_packets()))
    return bytearray(lgfxd.gfxd_macro_data().contents)

lgfxd.gfxd_macro_id.argtypes = None
lgfxd.gfxd_macro_id.restype = c_int
def gfxd_macro_id():
    """
    Returns a number that uniquely identifies the current macro.
    """
    return lgfxd.gfxd_macro_id()

lgfxd.gfxd_macro_name.argtypes = None
lgfxd.gfxd_macro_name.restype = c_char_p
def gfxd_macro_name():
    """
    Returns the name of the current macro. If the macro does not have a name (i.e. it's invalid), None is returned.
    
    If a dynamic display list pointer has been specified, the dynamic g version is returned.
    Otherwise the static gs version is returned.
    """
    return lgfxd.gfxd_macro_name().decode('utf-8')

lgfxd.gfxd_arg_count.argtypes = None
lgfxd.gfxd_arg_count.restype = c_int
def gfxd_arg_count():
    """
    Returns the number of arguments to the current macro, not including a dynamic display list pointer if one has been specified.
    """
    return lgfxd.gfxd_arg_count()

lgfxd.gfxd_arg_type.argtypes = [c_int]
lgfxd.gfxd_arg_type.restype = c_int
def gfxd_arg_type(arg_num: int):
    """
    Returns a number that identifies the type of the argument with index arg_num.
    """
    return lgfxd.gfxd_arg_type(c_int(arg_num))

lgfxd.gfxd_arg_name.argtypes = [c_int]
lgfxd.gfxd_arg_name.restype = c_char_p
def gfxd_arg_name(arg_num: int):
    """
    Returns the name of the argument with index arg_num. Argument names are not canonical,
    nor are they needed for macro disassembly, but they can be useful for informational and diagnostic purposes.
    """
    return lgfxd.gfxd_arg_name(c_int(arg_num)).decode('utf-8')

lgfxd.gfxd_arg_fmt.argtypes = [c_int]
lgfxd.gfxd_arg_fmt.restype = c_int
def gfxd_arg_fmt(arg_num: int):
    """
    Returns the data format of the argument with index arg_num.

    The return value will be
        gfxd_argfmt_i for int32_t
        gfxd_argfmt_u for uint32_t
        gfxd_argfmt_f for float

    When accessing the value of the argument with gfxd_arg_value, the member with the corresponding type should be used.
    """
    return lgfxd.gfxd_arg_fmt(c_int(arg_num))

lgfxd.gfxd_arg_value.argtypes = [c_int]
lgfxd.gfxd_arg_value.restype = POINTER(c_int * 1)
def gfxd_arg_value(arg_num: int):
    """
    Returns a tuple of different representations of the argument value:
        (signed int, unsigned int, float)
    """
    raw = lgfxd.gfxd_arg_value(arg_num).contents[0]
    return (struct.unpack(">i", struct.pack(">I", raw))[0], raw, struct.unpack(">f", struct.pack(">I", raw))[0])

lgfxd.gfxd_value_by_type.argtypes = None
lgfxd.gfxd_value_by_type.restype = POINTER(c_uint32 * 1)
def gfxd_value_by_type(type: int, idx: int):
    """
    Returns a tuple of different representations of the argument value:
        (signed int, unsigned int, float)
    """
    raw = lgfxd.gfxd_value_by_type(type, idx).contents[0]
    return (struct.unpack(">i", struct.pack(">I", raw))[0], raw, struct.unpack(">f", struct.pack(">I", raw))[0])

lgfxd.gfxd_arg_valid.argtypes = [c_int]
lgfxd.gfxd_arg_valid.restype = c_int
def gfxd_arg_valid(arg_num: int):
    """
    Returns non-zero if the argument with index arg_num is "valid", for some definition of valid.

    An invalid argument generally means that the disassembler found inconsistencies in the input data,
    or that the data can not be reproduced by the current macro type.

    The argument still has a value that can be printed, though the value is not guaranteed to make any sense.
    """
    return lgfxd.gfxd_arg_valid(c_int(arg_num)) != 0

# ====================================================================
#   Custom Output
# ====================================================================

lgfxd.gfxd_write.argtypes = [c_void_p]
lgfxd.gfxd_write.restype = c_int
def gfxd_write(data: bytes):
    """
    Insert count bytes from the buffer at buf into the output.

    The number of characters written is returned.
    """
    buffer = create_string_buffer(data, len(data))
    __gfxd_buffers_callbacks.update({10001 : buffer})
    return lgfxd.gfxd_write(c_char_p(buffer), len(buffer))

lgfxd.gfxd_puts.argtypes = [c_char_p]
lgfxd.gfxd_puts.restype = c_int
def gfxd_puts(string: str):
    """
    Insert the string into the output.

    The number of characters written is returned.
    """
    return lgfxd.gfxd_puts(c_char_p(string.encode("utf-8")))

lgfxd.gfxd_printf.argtypes = [c_char_p]
lgfxd.gfxd_printf.restype = c_int
def gfxd_printf(string: str):
    """
    Insert the printf-formatted string described by fmt and additional
    arguments into the output. Limited to 255 characters.

    The number of characters written is returned.
    """
    if len(string) > 255:
        raise GfxdArgumentError("gfxd_printf: len(string) > 255", "gfxd_printf is limited to 255 characters")

    return lgfxd.gfxd_printf(c_char_p(string.encode("utf-8")))

lgfxd.gfxd_print_value.argtypes = [c_int, POINTER(c_int32)]
lgfxd.gfxd_print_value.restype = c_int
def gfxd_print_value(type: int, value: Tuple[int, int, float]):
    """
    Insert the type-formatted value into the output.

    The number of characters written is returned.

    The macro argument with index n can be printed with
        gfxd_print_value(gfxd_arg_type(n), gfxd_arg_value(n))
    """
    return lgfxd.gfxd_print_value(type, byref(c_int32(value[0])))

# ====================================================================
#   Python Utilities
# ====================================================================

def gfxd_buffer_to_string(buffer: c_void_p):
    """
    Primary purpose is to fetch the contents of the output buffer as a python string.
    """
    return buffer.value.decode('utf-8')
