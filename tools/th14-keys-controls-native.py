"""Execute retail45c520 and its unchanged45d3c0 reassignment helper."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  begin=b&~4095;m.mem_map(begin,((b+size+4095)&~4095)-begin);m.mem_write(b,img.data[raw:raw+n])
 base,menu,stack,buttons=0x70000000,0x70001000,0x700ff000,0x70010000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 sounds=[];interrupts=[];refresh=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);pop=None
  if a==0x458d70:put(menu+0x2c8+get(sp+4)*4,1002);pop=4
  elif a==0x45c800:refresh.append(1);pop=0
  elif a==0x45d4c0:pop=0
  elif a==0x401b90:uc.reg_write(UC_X86_REG_EAX,buttons);pop=0
  elif a==0x46e3d0:sounds.append(get(sp+4));pop=8
  elif a in (0x47f140,0x47f1b0):interrupts.append([get(sp+4),get(sp+8)]);pop=8
  elif a==0x458c80:put(menu+0x1c,get(sp+4));put(menu+0x24,0);pop=4
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def case(state=2,timer=17,selected=0,pressed=0,repeat=0,buttons=0,edited=None):
  return dict(state=state,timer=timer,previous=timer-1,selected=selected,pressed=pressed,repeat=repeat,buttons=buttons,edited=edited or [4,3,2,1,0,0],config=[0,1,2,3,14,15,16,17,18,19])
 cases=[case(state=s,timer=t,selected=n) for s,t,n in [(0,0,0),(1,6,0),(1,7,0),(4,9,5),(4,10,5)]]
 keys=[(0,0),(1,0),(2,0),(256,0),(0x80000,0),(16,0),(32,0),(48,0),(0,16),(0,32),(1|16,0),(1|32,0),(3,0),(0x102|0x80001,0)]
 cases.extend(case(selected=n,pressed=k,repeat=r) for n,(k,r) in itertools.product(range(6),keys))
 cases.extend(case(selected=n,buttons=1<<b,edited=e) for n,b,e in itertools.product(range(6),range(31),([4,3,2,1,0,0],[7,7,7,7,7,7],[30,0,10,20,0,30])))
 cases.extend(case(selected=n,pressed=k,buttons=(1<<b)|(1<<30)) for n,k,b in itertools.product(range(6),(1,2,16,32,48,0x80001|0x102),range(5)))
 rows=[]
 for c in cases:
  m.mem_write(base,bytes(0xfe000));sounds.clear();interrupts.clear();refresh.clear()
  for off,v in ((0x1c,4),(0x24,c['state']),(0x28,c['selected']),(0x30,6),(0x34,2),(0x74,5),(0xb4,1),(0xf8,1),(0x2b4,c['previous']),(0x2b8,c['timer']),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1),(0x2d0,1002)):put(menu+off,v)
  m.mem_write(menu+0x5ad8,struct.pack('<6h',*c['edited']));table=struct.pack('<10h',*c['config']);m.mem_write(0x4d6aac,table);m.mem_write(0x4d9138,table)
  m.mem_write(buttons,bytes(128 if c['buttons']&(1<<i) else 0 for i in range(31)))
  put(0x4d8f58,0x3f800000);put(0x4d6884,c['pressed']);put(0x4d6880,c['repeat']);put(stack,base)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x45c520,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  rows.append(dict(input=c,result=dict(screen=get(menu+0x1c),state=get(menu+0x24),cursor=[get(menu+0x28),get(menu+0x30),get(menu+0xb4)],config=list(struct.unpack('<10h',m.mem_read(0x4d9138,20))),edited=list(struct.unpack('<6h',m.mem_read(menu+0x5ad8,12))),sounds=sounds[:],root=interrupts[-1][1] if interrupts else 0,refresh=bool(refresh))))
 path=ROOT/'artifacts/th14/keys-controls-native-oct11.json'
 path.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Complete retail45c520 callback and unchanged45d3c0 button reassignment, real cursor/history/timer helpers. Controller31-byte input, ANM creation/interrupt/digit refresh45c800/presentation45d4c0, audio delivery and screen transition are controlled boundaries. Live controller table initially equals config, as at normal startup; OS controller polling and GPU pixels excluded.'),indent=2)+'\n',encoding='utf-8')
 print(f'PASS {len(rows)} retail Key Config control cases')
if __name__=='__main__':main()
