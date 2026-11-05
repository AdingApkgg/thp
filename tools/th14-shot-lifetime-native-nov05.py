"""Run retail shot update and quad geometry on bounded model-state inputs.

This is a component oracle with controlled ANM lookup/release and cookie return.
It is not a capture of original gameplay and never supplies values to the port.
"""
from pathlib import Path
import hashlib, importlib, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX,
    UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_MXCSR, UC_X86_REG_FPCW,
    UC_X86_REG_FPSW, UC_X86_REG_FPTAG)

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/shot-lifetime-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()
sys.path.insert(0,str(R/'tools'))
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert SHA(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,offset,n in im.sections:
    first=base&~4095
    m.mem_map(first,((base+size+4095)&~4095)-first)
    m.mem_write(base,im.data[offset:offset+n])
END,OBJ,SPEC,PLAYER,VM,STACK=0x70000000,0x70001000,0x70002000,0x70010000,0x70040000,0x700ff000
m.mem_map(END,0x100000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
f=lambda word:struct.unpack('<f',struct.pack('<I',word))[0]
fp=lambda p,value:m.mem_write(p,struct.pack('<f',value))
events=[];quad=[]


def hook(machine,address,size,user):
    if address==0x47f0a0:
        events.append('lookup');m.reg_write(UC_X86_REG_EAX,VM)
    elif address==0x47f6e0:
        events.append('release');put(m.reg_read(UC_X86_REG_ECX),0)
    elif address==0x45115f:
        quad[:] = struct.unpack('<12I',m.mem_read(m.reg_read(UC_X86_REG_EBP)-0x34,48))


for address,cleanup in [(0x47f0a0,4),(0x47f6e0,0),(0x4854a0,0)]:
    m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
    m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
m.hook_add(UC_HOOK_CODE,hook,begin=0x45115f,end=0x45115f)
indices={case:json.loads((H/case/'model/shot-lifetime-index.json').read_bytes())['snapshots'] for case in ['baseline','late']}
bindings={}


def row(case,frame,slot):
    item=next(x for x in indices[case] if x['stage']==3 and x['stageFrame']==frame)
    path=H/case/'model'/item['file'];data=path.read_bytes()
    assert SHA(data)==item['sha256']
    bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data))
    return struct.unpack_from('<96I',data,slot*96*4)


def run(case,frame,slot,swap=False):
    r=row(case,frame,slot)
    assert r[1]==2 and r[25] and r[19]==0 and r[22]==0 and r[36]==0
    m.mem_write(END,bytes(0xf0000));events.clear();quad.clear()
    fields={0x10:r[7],0x14:1,0x18:r[4],0x1c:r[5],0x20:r[6],
        0x24:0x4d8f58,0x98:r[1],0xbc:SPEC}
    fields.update({0x54+i*4:r[12+i] for i in range(3)})
    fields.update({0x88:r[15],0x8c:r[16],0x6c:r[17],0x70:r[18]})
    for offset,value in fields.items():put(OBJ+offset,value)
    # Callback zero, motion mode zero, no damage area or extra VM.
    m.mem_write(SPEC+0x21,bytes([r[19]]))
    # Portable drawing/anchor fields occupy different bits from retail +18.
    native_flags=(r[29]&15)|(((r[29]>>18)&3)<<21)|(((r[29]>>20)&3)<<23)|(r[38]<<25)
    put(VM+0x18,native_flags)
    mapping={0x1c:30,0x50:49,0x60:50,0x64:51,0x68:52,0x6c:53,
        0x80:54,0x84:55,0x90:56,0x94:57,0x59c:40,0x5a0:41,0x5a4:42,
        0x3c:43,0x40:44,0x44:45,0x4ec:46,0x4f0:47,0x4f4:48}
    for offset,index in mapping.items():put(VM+offset,r[index])
    if swap:
        other=row('late' if case=='baseline' else 'baseline',frame,slot)
        put(VM+0x50,other[49])
    for p,value in [(0x4db67c,PLAYER),(0x4f7a70,128),(0x4f7a74,16),
        (0x4f7a88,320),(0x4f7a8c,16),(0x4f7a80,320),(0x4f7a84,16)]:put(p,value)
    fp(0x4f7a6c,1);fp(0x4d8f58,1)
    put(STACK,END);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OBJ)
    m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f)
    m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x4510b0,END,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==END and len(quad)==12
    retired=get(OBJ+0x98)==0
    expected=not bool(r[67])
    if swap:expected=not bool(other[67])
    assert retired==expected,(case,frame,slot,swap,retired,expected)
    assert ('release' in events)==retired and events.count('lookup')==1
    if not swap:
        expected_quad=r[68:80]
        error=max(abs(f(x)-f(y)) for x,y in zip(quad,expected_quad))
        assert tuple(quad)==expected_quad,(case,frame,error)
    else:error=None
    return dict(case=case,stage=3,stageFrame=frame,slot=slot,rotationSwapped=swap,
        retired=retired,expectedRetirement=expected,releaseCalled=retired,
        quadMaxAbsError=error,quadBitIdentical=(None if swap else True),retailWholeShotUpdateExecuted=True,
        retailQuadExecuted=True,originalGameplayCapture=False)


rows=[]
for slot,frame,retained in [(216,1478,'late'),(234,2092,'baseline')]:
    for case in ['baseline','late']:
        rows.append(run(case,frame,slot))
        rows.append(run(case,frame,slot,True))
    rows.append(run(retained,frame+1,slot))
out=dict(schema='th14/shot-lifetime-retail-component/1',passed=True,
    executableSha256=SHA(im.data),cases=rows,rotationOnlyControls=4,
    inputScope='Selected portable pre-Player snapshots mapped to retail fields',
    sinks=['ANM lookup','ANM release','security-cookie return'],
    originalGameplayPerSlotObserved=False,productionChanged=False,
    originalNineDifferencesClosed=False,completeGame=False,nativeEquivalent=False,
    evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),
    instructionBindings=[dict(pc=hex(pc),bytes=size,sha256=SHA(im.read(pc,size)))
        for pc,size in [(0x4510b0,0x2ca),(0x479560,0x100)]])
(H/'retail-component.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,cases=len(rows),rotationOnlyControls=4,
    originalGameplayCapture=False,productionChanged=False,completeGame=False)))
