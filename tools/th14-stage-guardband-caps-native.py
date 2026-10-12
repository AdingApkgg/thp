"""Read installed HAL guard-band and interpolation capabilities via SDK layouts."""
import ctypes as C,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared');caps_bytes=(sdk/'d3d9caps.h').read_bytes();caps_text=caps_bytes.decode();body=caps_text.split('typedef struct _D3DCAPS9',1)[1].split('float   ExtentsAdjust;',1)[0];body=re.sub(r'/\*.*?\*/','',body,flags=re.S);body=re.sub(r'//[^\n]*','',body);fields=[]
for typ,names in re.findall(r'(D3DDEVTYPE|UINT|DWORD|float)\s+([^;]+);',body):
    for name in names.split(','):fields.append((name.strip(),C.c_float if typ=='float' else C.c_uint32))
class Prefix(C.Structure):_fields_=fields
assert [n for n,_ in fields][-4:]==['GuardBandLeft','GuardBandTop','GuardBandRight','GuardBandBottom']
header=(sdk/'d3d9.h').read_text();body=header.split('DECLARE_INTERFACE_(IDirect3D9,',1)[1].split('};',1)[0];methods=[a.strip() or b.strip() for a,b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
dll=C.WinDLL('d3d9');dll.Direct3DCreate9.argtypes=[C.c_uint32];dll.Direct3DCreate9.restype=C.c_void_p;obj=C.c_void_p(dll.Direct3DCreate9(32));assert obj;table=C.cast(obj,C.POINTER(C.POINTER(C.c_void_p))).contents;storage=C.create_string_buffer(4096)
try:
    get=C.WINFUNCTYPE(C.c_long,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p)(table[methods.index('GetDeviceCaps')]);assert get(obj,0,1,storage)>=0;prefix=Prefix.from_buffer(storage);values={name:getattr(prefix,name) for name,_ in fields};sha=lambda b:hashlib.sha256(b).hexdigest()
    report=dict(queried=True,completeGame=False,nativeEquivalent=False,values=values,prefixBytes=C.sizeof(Prefix),offsets={name:getattr(Prefix,name).offset for name,_ in fields},toolSha256=sha(Path(__file__).read_bytes()),capsHeaderSha256=sha(caps_bytes),d3dHeaderSha256=sha((sdk/'d3d9.h').read_bytes()),d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),scope='Read-only default HAL SDK capability query; reported caps alone do not prove per-draw clipping or interpolation behavior.')
    (ROOT/'docs/porting/th14-stage-guardband-caps-observed-oct12.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:values[k] for k in ('GuardBandLeft','GuardBandTop','GuardBandRight','GuardBandBottom','RasterCaps','PrimitiveMiscCaps')}))
finally:C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(table[methods.index('Release')])(obj)
