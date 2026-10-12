"""Read ECL -9908 through both actual retail getters and its complete list counter."""
import sys,importlib,struct,json,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in im.sections:
 first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,im.data[raw:raw+n])
BASE=0x70000000;m.mem_map(BASE,0x300000);MANAGER=BASE+0x1000;OWNER=BASE+0x2000;STACK=BASE+0x2ff000;RETURN=BASE+0x2fe000;RESULT=RETURN+128
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
m.mem_write(RETURN,b'\xd9\x1d'+struct.pack('<I',RESULT));put(0x4db544,MANAGER)
cases=[[]]+[[(flags,immune)] for flags in range(64) for immune in [-2,0,1,2]]
for size in [2,7,16,64]:
 for seed in range(32):cases.append([(((seed*31+i*11)&63)|((i%3)*0x400000),(i*7+seed)%5-2) for i in range(size)])
rows=[]
for entries in cases:
 put(MANAGER+0xd0,BASE+0x4000 if entries else 0)
 for i,(flags,immune) in enumerate(entries):
  node=BASE+0x4000+i*16;enemy=BASE+0x8000+i*0x6000;put(node,enemy);put(node+4,node+16 if i+1<len(entries) else 0);put(enemy+0x5244,flags);put(enemy+0x51e0,immune)
 out=[]
 for address,float_result in [(0x42a920,False),(0x42b230,True)]:
  put(STACK,RETURN);put(STACK+4,-9908);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OWNER);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,RETURN+6 if float_result else RETURN,count=10000)
  assert m.reg_read(UC_X86_REG_EIP)==(RETURN+6 if float_result else RETURN);out.append(get(RESULT) if float_result else m.reg_read(UC_X86_REG_EAX))
 rows.append(dict(entries=entries,integer=out[0],floating=out[1]))
root=Path(__file__).resolve().parents[1];dest=root/'artifacts/th14/enemy-target-count';dest.mkdir(parents=True,exist_ok=True)
r=dict(passed=True,completeGame=False,nativeEquivalent=False,cases=rows,nativeExecutableSha256=hashlib.sha256(im.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual42a920/42b230 getters call complete4219b0; linked enemy inputs with varied flags and signed immunity, no lookup stub or Python output model. Isolated memory case proof, not live battle.')
(dest/'native.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('PASS',len(rows),'native count getter cases')
