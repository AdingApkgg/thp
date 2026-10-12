"""Locally authored D3D9 vertex arithmetic probes; no production shader changes."""
import ctypes as C,sys
from pathlib import Path
P,U=C.c_void_p,C.c_uint32
MODE='rcp-scalar'
assert MODE=='rcp-scalar' or MODE in ('rsq-rcp-mad','rsq-mul-mad','rsq-rcp-sub','rsq-rcp-divide-end','rsq-output','rcp-output')
def shader():
    root=Path(__file__).resolve().parent.parent;out=root/'artifacts/th14/gpu-native-shader-probe'/MODE;out.mkdir(parents=True,exist_ok=True)
    code="""vs_2_0
dcl_position v0
dcl_color v1
dcl_texcoord v2
m4x4 r0, v0, c0
m4x4 r4, r0, c4
m4x4 oPos, r4, c8
mov oD0, v1
mov oT0, v2
rcp oFog, c14.x
"""
    (out/'probe.asm').write_text(code,encoding='ascii')
    dll=C.WinDLL('d3dcompiler_47');dll.D3DAssemble.argtypes=[P,C.c_size_t,C.c_char_p,P,P,U,C.POINTER(P),C.POINTER(P)];dll.D3DAssemble.restype=C.c_int32
    bytecode=P();errors=P();source=C.create_string_buffer(code.encode('ascii'))
    def pointer(obj,index,result,*args):
        return C.WINFUNCTYPE(result,P,*args)(C.cast(obj,C.POINTER(C.POINTER(P))).contents[index])
    try:
        hr=dll.D3DAssemble(source,len(code),b'local-probe.asm',None,None,0,C.byref(bytecode),C.byref(errors))
        if hr<0:
            detail=C.string_at(pointer(errors,3,P)(errors),pointer(errors,4,C.c_size_t)(errors)) if errors.value else b''
            raise RuntimeError((hex(hr&0xffffffff),detail.decode('utf8','replace')))
        data=C.string_at(pointer(bytecode,3,P)(bytecode),pointer(bytecode,4,C.c_size_t)(bytecode));(out/'probe.vso').write_bytes(data)
        return data
    finally:
        for obj in (errors,bytecode):
            if obj.value:pointer(obj,2,U)(obj)
