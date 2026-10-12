"""Complete retail45ad90 row presentation, including its inline digit lookup."""
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
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 ids=list(range(23,49));vms={1000:root,**{i:arena+0x10000+i*0x1000 for i in ids}};events=[]
 def hook(uc,a,n,u):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0))
  elif a==0x458fa0:assert get(sp+4)==1;events.append([get(sp+8),get(sp+12)])
  elif a==0x46fe50:vm=m.reg_read(UC_X86_REG_ECX);events.append([get(vm+0x540),get(vm+0x4a0)]);m.reg_write(UC_X86_REG_EAX,0)
 for a,pop in [(0x47f0a0,4),(0x458fa0,12),(0x46fe50,0)]:
  m.mem_write(a,b'\xc2'+struct.pack('<H',pop));m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for selected in range(5):
  m.mem_write(menu,bytes(0x7000));m.mem_write(root,bytes(0x1000));events.clear();put(menu+0x28,selected);put(menu+0x2cc,1000);put(0x4f56cc,arena+0x70000)
  put(root+0x580,root);put(root+0x584,vms[ids[0]]+0x580)
  for index,i in enumerate(ids):
   vm=vms[i];m.mem_write(vm,bytes(0x1000));put(vm+0x540,i);m.mem_write(vm+0x4aa,struct.pack('<H',i));put(vm+0x580,vm);put(vm+0x584,vms[ids[index+1]]+0x580 if index+1<len(ids) else 0)
  put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x45ad90,arena,count=100000);assert m.reg_read(UC_X86_REG_EIP)==arena
  rows.append(dict(selected=selected,interrupts=events[:]))
 (ROOT/'artifacts/th14/options-presentation-native-oct11.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows,scope='Complete retail45ad90 with unchanged inline family traversal; controlled47f0a0 lookup,458fa0 child immediate-interrupt and46fe50 ANM update boundary. Exposes exact script/label delivery, not GPU pixels.'),indent=2)+'\n',encoding='utf-8');print('PASS 5 retail Option presentation routes')
if __name__=='__main__':main()
