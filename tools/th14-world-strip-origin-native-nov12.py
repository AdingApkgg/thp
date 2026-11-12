"""Execute the original world-strip translation prefix for supported display contexts."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
H=R/'artifacts/th14/world-strip-origin-nov12';H.mkdir(exist_ok=False)
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,b,size,raw,n in im.sections:
    first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,im.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x10000);vm=B+0x1000;matrix=B+0x2000;stack=B+0xe000
put=lambda p,v:m.mem_write(p,struct.pack('<I',v));floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
contexts=json.loads((R/'artifacts/th14/display-mode-entry-nov12/context-native-v2/report.json').read_bytes())
rows=[]
for width,flags,parent,position,route in itertools.product((640,960,1280),(0,0x20000,0x40000,0x60000),(0,1),((17.25,-9.5,.125),(-190,440,9),(24.25,230.5,-3)),range(3)):
    # Global play origin comes from the already executed, real compositor Begin.
    context=next(x for x in contexts['rows'] if x['mode']=={640:3,960:4,1280:5}[width] and x['resource']==1)
    origin=struct.unpack('<f',struct.pack('<I',context['stages'][1][1]))[0];assert origin==width//2
    m.mem_write(vm,bytes(0x600));put(vm+0x18,3);put(vm+0x1c,flags);put(vm+0x594,parent)
    script=[1.125,-2.5,3.75];child=[-4.25,6.5,-8.125]
    floats(vm+0x59c,position);floats(vm+0x3c,script);floats(vm+0x4ec,child);put(0x4f7a88,int(origin))
    value=[0.0]*16
    for i in (0,5,10,15):value[i]=1.0
    # Upstream native scale producer is outside this prefix; identical scales
    # are supplied to both sides, while the real C++ renderer computes its own.
    value[0]=2.25;value[5]=.75;floats(matrix,value)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,vm);m.reg_write(UC_X86_REG_ESI,matrix)
    m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x4785ab,0x478654,count=300)
    assert m.reg_read(UC_X86_REG_EIP)==0x478654
    expected=list(struct.unpack('<16I',m.mem_read(stack+0x98,64)))
    rows.append(dict(width=width,flags=flags,parent=parent,position=position,script=script,child=child,route=route,origin=origin,words=expected))
report=dict(rows=rows,cases=len(rows),executableSha256=sha(im.data),toolSha256=sha(Path(__file__).read_bytes()),
    functionSliceSha256=sha(im.read(0x4785ab,0x478654-0x4785ab)),contextReportSha256=sha((R/'artifacts/th14/display-mode-entry-nov12/context-native-v2/report.json').read_bytes()),
    originalInstructionsUnmodified=True,externalD3dCallNotExecuted=True,syntheticVmAndInitialMatrix=True,wholeNativeCallbackAccepted=False,
    scope='Original4783f0 translation producer4785ab..478654, supported resource-present compositor Begin origins only. No original rotation/scale producer, material/GPU/geometry/pixels claim.',completeGame=False)
(H/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps(dict(cases=len(rows),matrixWords=len(rows)*16,originalInstructionsUnmodified=True)))
