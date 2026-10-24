from pathlib import Path
import sys,importlib,json,struct,itertools,hashlib
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP
root=Path(__file__).resolve().parents[1];h=root/'artifacts/th14/paused-score-check';h.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'));img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in img.sections:
 a=base&~4095;m.mem_map(a,((base+size+4095)&~4095)-a);m.mem_write(base,img.data[raw:raw+n])
base=0x70000000;hud=base+0x1000;stack=base+0x1f000;m.mem_map(base,0x20000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];cases=[]
for current,displayed,speed,flags in itertools.product((0,1,31,32,10000000,73241120,999999999),(0,1,35941120,999999999),(0,1,578910),(0,0x10,0x40,0x108)):
 high=12345;continues=3;put(0x4db550,hud);put(hud+0x140,displayed);put(hud+0x144,speed);put(0x4f5830,current);put(0x4f5838,continues);put(0x4f5898,high);put(0x4f589c,1);put(0x4f58b8,flags);put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x434360,base,count=1000);assert m.reg_read(UC_X86_REG_EIP)==base
 cases.append(dict(current=current,displayed=displayed,speed=speed,high=high,continues=continues,highContinues=1,flags=flags,result=[get(hud+0x140),get(hud+0x144),get(0x4f5898),get(0x4f589c),get(0x4f58b8)]))
(h/'native.json').write_text(json.dumps(dict(originalExecutableSha256=hashlib.sha256(img.data).hexdigest(),originalEntry='434360',instructionBytesPatched=0,controlledHudAndGlobals=True,cases=cases),indent=2)+'\n');print('Unmodified original score callback cases:',len(cases))
