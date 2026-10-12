"""Read hardware support for a separately scoped lockable-depth diagnostic."""
import ctypes as C,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
header=sdk.read_text(encoding='utf8');body=header.split('DECLARE_INTERFACE_(IDirect3D9,',1)[1].split('};',1)[0]
names=[a.strip() or b.strip() for a,b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
assert names.index('CheckDeviceFormat')==10
dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=C.c_void_p;dll.Direct3DCreate9.argtypes=[C.c_uint]
device=C.c_void_p(dll.Direct3DCreate9(32));assert device
table=C.cast(device,C.POINTER(C.POINTER(C.c_void_p))).contents
class DisplayMode(C.Structure):_fields_=[(n,C.c_uint) for n in ('width','height','refresh','format')]
assert names.index('GetAdapterDisplayMode')==8
mode=DisplayMode()
get_mode=C.WINFUNCTYPE(C.c_long,C.c_void_p,C.c_uint,C.POINTER(DisplayMode))(table[8])
assert get_mode(device,0,C.byref(mode))>=0
check=C.WINFUNCTYPE(C.c_long,C.c_void_p,*([C.c_uint]*6))(table[10])
release=C.WINFUNCTYPE(C.c_long,C.c_void_p)(table[2])
try:
    rows=[]
    for format,name in ((80,'D16'),(70,'D16_LOCKABLE')):
        result=check(device,0,1,mode.format,2,1,format)
        rows.append(dict(format=format,name=name,hresult=result&0xffffffff,supported=result>=0))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    report=dict(queried=True,completeGame=False,nativeEquivalent=False,processBits=C.sizeof(C.c_void_p)*8,adapter=0,deviceType=1,adapterFormat=mode.format,usage=2,resourceType=1,formats=rows,
                toolSha256=sha(Path(__file__).read_bytes()),sdkSha256=sha(sdk.read_bytes()),d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),
                scope='Read-only D3D9 capability query for this installed default HAL. Support does not establish creation, lock success, matching D16 behavior or retail depth readback.')
    (ROOT/'docs/porting/th14-stage-depth-format-observed-oct12.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(rows))
finally:release(device)
