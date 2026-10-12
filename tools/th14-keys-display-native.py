"""Retail45c800 digit binding and45d4c0 row presentation helpers."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  begin=b&~4095;m.mem_map(begin,((b+size+4095)&~4095)-begin);m.mem_write(b,im.data[raw:raw+n])
 arena,menu,root,stack=0x70000000,0x70001000,0x70008000,0x700ff000;m.mem_map(arena,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 ids=list(range(49,77));vms={1000:root,**{i:arena+0x10000+i*0x1000 for i in ids}};binds=[];events=[]
 def hook(uc,address,n,u):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0))
  elif address==0x46f1e0:binds.append([get(get(sp+4)+0x540),get(sp+8)])
  elif address==0x458fa0:events.append([get(sp+4),get(sp+8),get(sp+12)])
 for address,pop in [(0x47f0a0,4),(0x46f1e0,8),(0x458fa0,12)]:
  m.mem_write(address,b'\xc2'+struct.pack('<H',pop));m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 def call(address):
  put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(address,arena,count=100000);assert m.reg_read(UC_X86_REG_EIP)==arena
 rows=[]
 for values in sorted(set(tuple(v if i==row else i for i in range(4)) for row in range(4) for v in range(31))):
  m.mem_write(menu,bytes(0x7000));m.mem_write(root,bytes(0x1000));binds.clear();put(menu+0x2d0,1000);put(0x4f56cc,arena+0x70000)
  m.mem_write(menu+0x5ad8,struct.pack('<4h',*values));put(root+0x580,root);put(root+0x584,vms[ids[0]]+0x580)
  for index,i in enumerate(ids):
   vm=vms[i];m.mem_write(vm,bytes(0x1000));put(vm+0x540,i);m.mem_write(vm+0x4aa,struct.pack('<H',i));put(vm+0x580,vm)
   put(vm+0x584,vms[ids[index+1]]+0x580 if index+1<len(ids) else 0)
  call(0x45c800);assert len(binds)==16
  rows.append(dict(values=values,bindings=binds[:]))
 presentation=[]
 for selected in range(6):
  put(menu+0x28,selected);events.clear();call(0x45d4c0);presentation.append(dict(selected=selected,interrupts=events[:]))
 (ROOT/'artifacts/th14/keys-display-native-oct11.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows,presentation=presentation,scope='Complete retail45c800 signed-i16 digit arithmetic on all31 assignable buttons in each of4 rows, and complete45d4c0 presentation-call order for all6 cursor rows. Native ANM lookup/binding and child immediate-interrupt delivery controlled; GPU pixels/physical controller polling excluded.'),indent=2)+'\n',encoding='utf-8')
 print(f'PASS {len(rows)} retail Key Config display cases and {len(presentation)} presentation routes')
if __name__=='__main__':main()
