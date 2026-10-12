"""Read the local D3D9 adapter identity for renderer precision provenance."""
import ctypes as C,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
P,U=C.c_void_p,C.c_uint32
dll=C.WinDLL('d3d9');dll.Direct3DCreate9.argtypes=[U];dll.Direct3DCreate9.restype=P
obj=P(dll.Direct3DCreate9(32));assert obj
table=C.cast(obj,C.POINTER(C.POINTER(P))).contents
try:
    buffer=C.create_string_buffer(2048)
    hr=C.WINFUNCTYPE(C.c_int32,P,U,U,P)(table[5])(obj,0,0,buffer);assert hr>=0
    raw=buffer.raw
    text=lambda off,size:raw[off:off+size].split(b'\0',1)[0].decode('mbcs','replace')
    report=dict(readOnly=True,driver=text(0,512),description=text(512,512),deviceName=text(1024,32),vendorId=int.from_bytes(raw[1064:1068],'little'),deviceId=int.from_bytes(raw[1068:1072],'little'),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Local D3D9 adapter identity; not browser adapter identity or rendering equivalence.')
    (ROOT/'docs/porting/th14-gpu-adapter-native-observed-oct11.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,ensure_ascii=False))
finally:C.WINFUNCTYPE(U,P)(table[2])(obj)
