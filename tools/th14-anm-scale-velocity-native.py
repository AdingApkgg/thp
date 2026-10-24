from pathlib import Path
import hashlib,json,struct,sys,importlib
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
root=Path(__file__).resolve().parents[1];home=root/'artifacts/th14/anm-scale-velocity-check';home.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'))
img,table,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in img.sections:
 start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
base=0x70000000;m.mem_map(base,0x20000);vm=base+0x1000;code=base+0x2000;stack=base+0x1f000;loop=0x47007e
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
rows=[]
for seed,visual in [(1,2),(12345,54321),(65535,0)]:
 for refs in range(4):
  for argument in (10010,10011,10012,10030,10031,10032):
   for flags2 in (0,0x820000):
    m.mem_write(vm,bytes(0x700));put(vm+0x18,7);put(vm+0x1c,flags2);put(vm+0x28,code)
    m.mem_write(vm+0x60,struct.pack('<ff',1,1));m.mem_write(vm+0x4e0,struct.pack('<ff',1,3.1415927410125732));m.mem_write(0x4db508,struct.pack('<HHIHHI',seed,0,0,visual,0,0))
    args=[float(argument)if refs&1 else .25,float(argument)if refs&2 else -.125]
    m.mem_write(code,struct.pack('<hHhHff',416,16,0,refs,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack);m.reg_write(UC_X86_REG_EDI,vm);m.reg_write(UC_X86_REG_EBX,code);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(table[416],loop,count=100000);assert m.reg_read(UC_X86_REG_EIP)==loop
    rows.append(dict(seed=seed,visualSeed=visual,refs=refs,argument=argument,initialFlags2=flags2,argsBits=list(struct.unpack('<2I',struct.pack('<2f',*args))),values=[get(vm+0x1c),get(vm+0x70),get(vm+0x74),get(0x4db508)&65535,get(0x4db50c),get(0x4db510)&65535,get(0x4db514)]))
report=dict(originalExecutableSha256=hashlib.sha256(img.data).hexdigest(),originalHandler=hex(table[416]),originalInstructionsUnmodified=True,controlledVmAndSeeds=True,handlerOnlyNotCompleteProcess=True,cases=rows)
(home/'native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(cases=len(rows),originalHandler=hex(table[416]),instructionsPatched=0)))
