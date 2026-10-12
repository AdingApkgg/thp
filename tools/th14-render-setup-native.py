"""Observe the whole retail render-state initializer and real HAL defaults."""
import importlib,importlib.util,json,hashlib,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()

def hardware_default():
    source=ROOT/'tools/th14-gpu-raster-native.py'
    spec=importlib.util.spec_from_file_location('gpu_types',source);types=importlib.util.module_from_spec(spec);spec.loader.exec_module(types)
    C,P,U,I=types.C,types.P,types.U,types.I
    header=types.SDK.read_text(encoding='utf8');tables={}
    for name in ('IDirect3D9','IDirect3DDevice9'):
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        tables[name]={method:index for index,method in enumerate([a.strip() or b.strip() for a,b in types.re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body)])}
    def method(obj,interface,name,args):
        address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        return C.WINFUNCTYPE(I,P,*args)(address)
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
    dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    window=None;d3d=P();device=P()
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 hidden state fixture',0,0,0,32,32,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=types.Present(32,32,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        assert method(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)])(d3d,0,1,window,64,C.byref(pp),C.byref(device))>=0
        states={}
        for key in (28,35,36,37,38,48,140):
            value=U();assert method(device,'IDirect3DDevice9','GetRenderState',[U,C.POINTER(U)])(device,key,C.byref(value))>=0;states[str(key)]=value.value
        assert states['48']==0
        return dict(deviceType=1,behaviorFlags=64,states=states,d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()),sdkHeaderSha256=sha(types.SDK.read_bytes()))
    finally:
        for obj,interface in ((device,'IDirect3DDevice9'),(d3d,'IDirect3D9')):
            if obj.value:method(obj,interface,'Release',[])(obj)
        if window:user.DestroyWindow(window)

def main():
    image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in image.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
    base,stop,stack,device,table,manager=0x70000000,0x70000100,0x7001f000,0x70002000,0x70003000,0x71000000
    m.mem_map(base,0x20000);m.mem_map(manager,0xc00000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    events=[];state={}
    def observe(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP);assert get(sp+4)==device
        if address==stop+0x10:
            key,value=get(sp+8),get(sp+12);events.append(['state',key,value]);state[key]=value
        else:
            events.append(['stage' if address==stop+0x20 else 'sampler',get(sp+8),get(sp+12),get(sp+16)])
        machine.reg_write(UC_X86_REG_EAX,0)
    put(device,table);put(0x4d8f68,device)
    for address,offset,args in ((stop+0x10,0xe4,12),(stop+0x20,0x10c,16),(stop+0x30,0x114,16)):
        put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',args));m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
    rows=[]
    for initial_range in (0,1):
        for live_manager in (False,True):
            state.clear();state[48]=initial_range;events.clear();put(0x4f56cc,manager if live_manager else 0);m.mem_write(manager+0xbc8188,b'\xa5'*12)
            put(stack,stop);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x46b650,stop,count=10000);assert m.reg_read(UC_X86_REG_EIP)==stop
            assert state[48]==initial_range and state[140]==3 and state[35]==0 and state[28]==1
            assert state[36]==0x447a0000 and state[37]==0x459c4000 and state[38]==0x3f800000
            assert len(events)==35,(len(events),events)
            rows.append(dict(initialRangeFog=initial_range,liveManager=live_manager,finalStates=state.copy(),events=events.copy(),managerCache=m.mem_read(manager+0xbc8188,12).hex()))
    report=dict(passed=True,completeGame=False,nativeEquivalent=False,entry='0x46b650',executableSha256=sha(image.data),functionSha256=sha(image.read(0x46b650,0x2ee)),toolSha256=sha(Path(__file__).read_bytes()),hardwareDefault=hardware_default(),rows=rows,limits='Complete original render-state initializer with only COM calls observed, plus separate real HAL default-state query. Linear vertex fog is configured and range fog is left unchanged; default range state is false. This does not establish every later draw-loop state or capture a native game frame.')
    (ROOT/'docs/porting/th14-render-setup-native-observed-oct11.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('Passed whole retail setup; real HAL default range fog is false')
if __name__=='__main__':main()
