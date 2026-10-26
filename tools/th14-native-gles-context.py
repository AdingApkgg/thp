"""A standalone Windows ANGLE EGL pbuffer; no application or browser control."""
import ctypes as C
import hashlib
import os
from pathlib import Path


def fn(library, name, result, *arguments):
    function = getattr(library, name)
    function.restype = result
    function.argtypes = list(arguments)
    return function


class Context:
    def __init__(self, directory):
        directory = Path(directory).resolve()
        self.dll_directory = os.add_dll_directory(str(directory))
        self.egl = C.WinDLL(str(directory / 'libEGL.dll'))
        self.gles = C.WinDLL(str(directory / 'libGLESv2.dll'))
        self.get_proc_address = fn(self.egl, 'eglGetProcAddress', C.c_void_p, C.c_char_p)
        error = fn(self.egl, 'eglGetError', C.c_uint)
        array = lambda *values: (C.c_int * len(values))(*values)
        get_display = C.WINFUNCTYPE(C.c_void_p, C.c_uint, C.c_void_p, C.POINTER(C.c_int))(self.get_proc_address(b'eglGetPlatformDisplayEXT'))
        # Explicit ANGLE D3D11 hardware device. No backend fallback.
        self.display = get_display(0x3202, None, array(0x3203, 0x3208, 0x3209, 0x320a, 0x3038))
        assert self.display, hex(error())
        major, minor = C.c_int(), C.c_int()
        assert fn(self.egl, 'eglInitialize', C.c_uint, C.c_void_p, C.POINTER(C.c_int), C.POINTER(C.c_int))(self.display, C.byref(major), C.byref(minor)), hex(error())
        assert fn(self.egl, 'eglBindAPI', C.c_uint, C.c_uint)(0x30a0)
        config, count = C.c_void_p(), C.c_int()
        choose = fn(self.egl, 'eglChooseConfig', C.c_uint, C.c_void_p, C.POINTER(C.c_int), C.POINTER(C.c_void_p), C.c_int, C.POINTER(C.c_int))
        assert choose(self.display, array(0x3033, 1, 0x3040, 0x40, 0x3024, 8, 0x3023, 8, 0x3022, 8, 0x3021, 8, 0x3025, 0, 0x3026, 0, 0x3038), C.byref(config), 1, C.byref(count)) and count.value == 1, hex(error())
        self.surface = fn(self.egl, 'eglCreatePbufferSurface', C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_int))(self.display, config, array(0x3057, 640, 0x3056, 480, 0x3038))
        assert self.surface, hex(error())
        self.context = fn(self.egl, 'eglCreateContext', C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_int))(self.display, config, None, array(0x3098, 3, 0x3038))
        assert self.context, hex(error())
        assert fn(self.egl, 'eglMakeCurrent', C.c_uint, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p)(self.display, self.surface, self.surface, self.context), hex(error())
        get_string = fn(self.gles, 'glGetString', C.c_char_p, C.c_uint)
        self.info = dict(renderer=get_string(0x1f01).decode(), version=get_string(0x1f02).decode(), vendor=get_string(0x1f00).decode(), glsl=get_string(0x8b8c).decode(), egl=[major.value, minor.value], extensions=get_string(0x1f03).decode().split(), libraries={name: dict(bytes=(directory / name).stat().st_size, sha256=hashlib.sha256((directory / name).read_bytes()).hexdigest()) for name in ['libEGL.dll', 'libGLESv2.dll']})

    def clip_control(self):
        assert 'GL_EXT_clip_control' in self.info['extensions'], 'Declared production profile requires EXT_clip_control'
        pointer = self.get_proc_address(b'glClipControlEXT')
        assert pointer
        C.WINFUNCTYPE(None, C.c_uint, C.c_uint)(pointer)(0x8ca1, 0x935f)
        assert fn(self.gles, 'glGetError', C.c_uint)() == 0
        return 1

    def close(self):
        fn(self.egl, 'eglMakeCurrent', C.c_uint, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p)(self.display, None, None, None)
        fn(self.egl, 'eglDestroyContext', C.c_uint, C.c_void_p, C.c_void_p)(self.display, self.context)
        fn(self.egl, 'eglDestroySurface', C.c_uint, C.c_void_p, C.c_void_p)(self.display, self.surface)
        fn(self.egl, 'eglTerminate', C.c_uint, C.c_void_p)(self.display)
