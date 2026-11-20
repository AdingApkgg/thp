from pathlib import Path
import sys,struct,json,hashlib,math
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import argparse
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser(description='TH14 original-instruction scaled circular collision boundary references; requires local original executable and Unicorn.');a.add_argument('--out',type=Path,required=True);options=a.parse_args();sys.path.insert(0,str(R/'tools'))
import importlib
img,*_=importlib.import_module('th-anm-handlers').handlers(14);exe=hashlib.sha256(img.data).hexdigest();assert exe=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,address,size,raw,n in img.sections:
 start=address&~4095;m.mem_map(start,((address+size+4095)&~4095)-start);m.mem_write(address,img.data[raw:raw+n])
end,player,hud,pos,header,stack=[0x70000000+n for n in (0,0x1000,0x20000,0x21000,0x23000,0x3f000)];m.mem_map(end,0x40000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
put(0x4db67c,player);put(0x4db550,hud);put(player+0x688,header);hits=[]
def hit(machine,address,size,user):
 assert machine.reg_read(UC_X86_REG_ECX)==player;hits.append(True);sp=machine.reg_read(UC_X86_REG_ESP);machine.reg_write(UC_X86_REG_EIP,get(sp));machine.reg_write(UC_X86_REG_ESP,sp+4)
m.hook_add(UC_HOOK_CODE,hit,begin=0x44f7a0,end=0x44f7a0)
rows=[];px,py=-12.25,80.5
for radius in (.75,1.25,2.1):
 for factor in (.5,1.,2.,3.5,8.):
  for scaled in (0,1):
   for width in (0.,1.,8.):
    # These formulas select test positions, never reference outcomes.
    # Outcomes always come from actual44efa0 machine code.
    requested=f32(f32(factor*f32(3.6))*f32(radius))if scaled else f32(radius)
    positions={f32(px+d)for d in (0,1,2,4,6,8,12,20,32,40,64,96)}
    for size in (radius,requested):
     center=f32(px+math.sqrt(f32(f32(size*size)+f32(width*width))))
     positions.update([center,f32(center-.25),f32(center+.25)])
     b=bits(center)
     if b not in (0,0x80000000):positions.update(f32(struct.unpack('<f',struct.pack('<I',b+d))[0])for d in (-1,1))
    for x in sorted(positions):
     for dialogue,probe in ((0,0),(0,1),(1,0)):
      hits.clear();put(player+0x5e0,bits(px));put(player+0x5e4,bits(py));put(header+4,bits(radius));put(player+0x182d4,16 if scaled else 0);put(player+0x18308,bits(factor));put(player+0x684,1);put(player+0x182c4,0);put(hud+0x194,dialogue);put(pos,bits(x));put(pos+4,bits(py));put(stack,end);put(stack+4,pos);put(stack+8,probe)
      m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,bits(width));m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x44efa0,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
      rows.append({'input':[1,*map(bits,(px,py,x,py,width,width*.75,radius,factor)),scaled,1,0,dialogue,probe],'result':[m.reg_read(UC_X86_REG_EAX),int(bool(hits))]})
q={'schema':'th14/retail-scaled-circle-edges/1','executableSha256':exe,'entry':'0x44efa0','instructionBytesPatched':0,'controlledBoundaries':['0x44f7a0 hit application recorded sink, ECX identity checked; unexecuted body returned without code patch'],'caseCount':len(rows),'positionsDerivedFromHypothesesOnly':True,'resultsFromActualNativeInstructions':True,'newOriginalGameProcess':False,'cases':rows}
options.out.write_text(json.dumps(q,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in q.items()if k!='cases'}),flush=True)
