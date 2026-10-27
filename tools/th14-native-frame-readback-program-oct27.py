"""Build a bounded x86 D3D9 readback program for one owned retail test child.

No process or UI is opened here. Callers must execute on the device's original
render thread after its draws and declare the diagnostic execution change.
All output slots are inside a caller-owned allocation. The original frame is
read before cleanup; the game must not resume after this diagnostic capture.
"""
from pathlib import Path
import hashlib,re,struct

def build(base,device,header):
    assert 0x10000<=base<0xffff0000 and 0<device<2**32 and base%4096==0
    raw=Path(header).read_bytes();text=raw.decode('utf8');tables={}
    for name in ('IDirect3DDevice9','IDirect3DSurface9'):
        body=text.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        methods=[a.strip()or b.strip()for a,b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)]
        tables[name]={method:index for index,method in enumerate(methods)}
    expected={'Present':17,'GetBackBuffer':18,'GetRenderTargetData':32,'CreateOffscreenPlainSurface':36}
    assert all(tables['IDirect3DDevice9'][key]==value for key,value in expected.items())
    assert [tables['IDirect3DSurface9'][key]for key in ('Release','GetDesc','LockRect','UnlockRect')]==[2,12,13,14]
    data=base+0x1000
    source,system,desc,lock,status=data,data+4,data+0x20,data+0x60,data+0x100
    imm=lambda value:('imm',value)
    mem=lambda address:('mem',address)
    def program(offset,calls):
        code=bytearray();branches=[];entries=[]
        for ordinal,(object_,interface,method,arguments,slot,check)in enumerate(calls):
            entries.append(dict(offset=offset+len(code),interface=interface,method=method,
                arguments=arguments,object=object_,statusSlot=slot,checksHresult=check))
            for kind,value in reversed(arguments):
                code.extend((b'\x68'if kind=='imm'else b'\xff\x35')+struct.pack('<I',value))
            kind,value=object_
            code.extend((b'\xb8'if kind=='imm'else b'\xa1')+struct.pack('<I',value))
            code.extend(b'\x8b\x08\x50\xff\x91'+struct.pack('<I',tables[interface][method]*4))
            code.extend(b'\xa3'+struct.pack('<I',status+slot*4))
            if check:
                code.extend(b'\x85\xc0\x0f\x88');branches.append(len(code));code.extend(bytes(4))
        stop=offset+len(code)
        code.extend(b'\xcc\xeb\xfe')
        for branch in branches:struct.pack_into('<i',code,branch,stop-(offset+branch+4))
        return bytes(code),base+stop,entries
    primary=[
        (imm(device),'IDirect3DDevice9','GetBackBuffer',[imm(0),imm(0),imm(0),imm(source)],0,True),
        (mem(source),'IDirect3DSurface9','GetDesc',[imm(desc)],1,True),
        (imm(device),'IDirect3DDevice9','CreateOffscreenPlainSurface',
            [mem(desc+24),mem(desc+28),mem(desc),imm(2),imm(system),imm(0)],2,True),
        (imm(device),'IDirect3DDevice9','GetRenderTargetData',[mem(source),mem(system)],3,True),
        (mem(system),'IDirect3DSurface9','LockRect',[imm(lock),imm(0),imm(16)],4,True),
    ]
    cleanup=[
        (mem(system),'IDirect3DSurface9','UnlockRect',[],5,True),
        (mem(system),'IDirect3DSurface9','Release',[],6,False),
        (mem(source),'IDirect3DSurface9','Release',[],7,False),
    ]
    first,first_stop,first_calls=program(0,primary)
    last,last_stop,last_calls=program(0x800,cleanup)
    assert len(first)<0x800 and len(last)<0x800
    code=first+bytes([0x90])*(0x800-len(first))+last
    initial=bytearray(0x1000)
    for index in range(8):struct.pack_into('<I',initial,0x100+index*4,0x7fffffff)
    return dict(code=code,initialData=bytes(initial),entry=base,cleanupEntry=base+0x800,
        captureStop=first_stop,cleanupStop=last_stop,data=data,sourceSlot=source,systemSlot=system,
        description=desc,lock=lock,status=status,allocationBytes=0x2000,codePageBytes=0x1000,
        methods=tables,primaryCalls=first_calls,cleanupCalls=last_calls,
        sdkSha256=hashlib.sha256(raw).hexdigest(),codeSha256=hashlib.sha256(code).hexdigest())
