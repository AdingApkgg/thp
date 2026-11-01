"""Execute intact451430 -> geometry ->414020, observing the unwritten polar Z."""
from pathlib import Path
import hashlib,importlib,itertools,json,struct,sys
import argparse
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();O=a.output.resolve();assert O.is_relative_to(R/'artifacts/th14')
O.mkdir(exist_ok=False);sys.path.insert(0,str(R/'tools'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from unicorn.x86_const import *
im,_,_=importlib.import_module('th-anm-handlers').handlers(14);SHA=lambda b:hashlib.sha256(b).hexdigest()
assert SHA(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,address,size,offset,length in im.sections:
    first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,im.data[offset:offset+length])
base=0x70000000;m.mem_map(base,0x100000)
end,player,bomb,resource,target,sizeptr,flag,last,visual=base,base+0x1000,base+0x20000,base+0x21000,base+0x22000,base+0x22020,base+0x22040,base+0x22060,base+0x30000
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
scratch=0;active=False;writes=[];reads=[];effects=[];entries=[];geometry=[]
def mem_hook(machine,access,address,size,value,user):
    if not active or not(address<=scratch and scratch+4<=address+size):return
    pc=m.reg_read(UC_X86_REG_EIP)
    if access==UC_MEM_READ:
        if pc==0x4140c7:reads.append(dict(pc=pc,address=address,size=size,scratch=scratch,value=get(scratch),lastOriginalWriter=writes[-1]if writes else None))
    else:writes.append(dict(pc=pc,address=address,size=size,word=(value>>(8*(scratch-address)))&0xffffffff))
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,mem_hook,begin=base+0xfd000,end=base+0xff100)
def code_hook(machine,pc,size,user):
    sp=m.reg_read(UC_X86_REG_ESP)
    if pc==0x414020:
        actual=((sp-4)&~7)-4;assert actual==scratch,(hex(sp),hex(actual),hex(scratch));entries.append(dict(pc=pc,esp=sp,scratch=actual));return
    if pc in (0x404ca0,0x4061f0):geometry.append(dict(pc=pc,esp=sp,returnPc=get(sp)));return
    assert pc==0x47ed10
    p=get(sp+12);effects.append(dict(script=get(sp+8),position=[get(p+i*4)for i in range(3)],positionAddress=p,rotation=get(sp+16)))
    m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_ESP,sp+32);m.reg_write(UC_X86_REG_EIP,get(sp))
for pc in [0x414020,0x404ca0,0x4061f0,0x47ed10]:m.hook_add(UC_HOOK_CODE,code_hook,begin=pc,end=pc)
rows=[]
for alignment,circle,rectangle,delta,seed,poison in itertools.product([0,4],[False,True],[False,True],[0.,8.],[0,1337],[0,0x3f800000]):
    active=False;stack=base+0xff000+alignment;s=stack-44;scratch=((s-4)&~7)-4
    for p,n in [(player,0x19000),(bomb,0x100),(resource,0x100),(stack-0x2000,0x2100)]:m.mem_write(p,bytes(n))
    put(0x4db67c,player);put(0x4db52c,bomb);put(0x4db53c,visual);put(visual+0x10,visual+0x100)
    put(player+0x688,resource);put(player+0x68c,9);put(player+0x690,10);put(resource+0x28,220);put(0x4f5830,0)
    put(0x4db508,seed);put(0x4db50c,0);put(0x4db510,54321);put(0x4db514,0);floats(0x4d8f58,1)
    floats(target,17+delta,123+delta,0);floats(sizeptr,48,32);put(flag,0);floats(last,0,0,0)
    a=player+0xde18
    for off,value in [(0x10,7 if circle else 5),(0x14,bits(64)),(0x1c,bits(.5)),(0x24,bits(96)),(0x28,bits(64)),(0x2c,bits(17)),(0x30,bits(123)),(0x34,0),(0x70,2),(0x74,3),(0x78,bits(3)),(0x84,19),(0x8c,9999999),(0x90,1),(0xa0,0x414020)]:put(a+off,value)
    args=[target,sizeptr if rectangle else 0,bits(8),flag,last,0,0,0];put(stack,end)
    for i,v in enumerate(args):put(stack+4+i*4,v)
    put(scratch,poison);writes.clear();reads.clear();effects.clear();entries.clear();geometry.clear()
    for reg,value in [(UC_X86_REG_ESP,stack),(UC_X86_REG_XMM3,bits(-.25)),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,value)
    active=True;m.emu_start(0x451430,end,count=300000);active=False
    assert m.reg_read(UC_X86_REG_EIP)==end and len(reads)==len(effects)==len(entries)==1
    assert effects[0]['script']==58 and effects[0]['position'][2]==reads[0]['value']
    rows.append(dict(alignment=alignment,areaCircle=circle,targetRectangle=rectangle,targetDelta=delta,seed=seed,priorScratch=poison,callback=entries[0],geometry=geometry[:],firstZRead=reads[0],factory=effects[0],damage=m.reg_read(UC_X86_REG_EAX),scriptRng=[get(0x4db508)&65535,get(0x4db50c)],originalSlotWrites=writes[:]))
assert len(rows)==64
report=dict(originalExecutableSha256=SHA(im.data),actualCollectorAndGeometryAndBombCallbackExecuted=True,originalInstructionBytesPatched=0,polarZNeverWrittenByObserverDuringExecution=True,factoryIsDeclaredRecordedReturnBoundary=True,syntheticStackAndPositionsDeclared=True,liveProcessOrCurrentCppNotAccepted=True,cases=rows,toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');(O/'run-tool.py').write_bytes(Path(__file__).read_bytes())
from collections import Counter
print(json.dumps(dict(cases=len(rows),lastOriginalWriterCounts={hex(k):v for k,v in Counter(r['firstZRead']['lastOriginalWriter']['pc']if r['firstZRead']['lastOriginalWriter']else 0 for r in rows).items()},nonzeroFactoryZ=sum(r['factory']['position'][2]!=0 for r in rows),productionSourcesModified=False)))
