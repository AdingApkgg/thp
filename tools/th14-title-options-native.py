"""Retail45b870 volume digits, retaining actual signed-byte arithmetic.

ANM lookup/child lookup/bind and audio delivery are controlled boundaries.
The native function traverses the supplied family and changes visibility itself.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in im.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,im.data[raw:raw+n])
 arena,menu,root,stack=0x70000000,0x70001000,0x70008000,0x700ff000;m.mem_map(arena,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 ids=[33,34,35,37,38,39,41,42,43,45,46,47]
 vms={1000:root,**{i:arena+0x10000+i*0x1000 for i in ids}}
 binds=[]
 def hook(uc,address,n,u):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0))
  elif address==0x4590b0:
   output,slot,script=get(sp+4),get(sp+8),get(sp+12)
   assert slot==1 and script in ids,(slot,script)
   put(output,script);m.reg_write(UC_X86_REG_EAX,output)
  elif address==0x46f1e0:
   vm,sprite=get(sp+4),get(sp+8);binds.append([get(vm+0x540),sprite])
 for address,pop in [(0x47f0a0,4),(0x4590b0,12),(0x46f1e0,8),(0x46ef90,12)]:
  m.mem_write(address,b'\xc2'+struct.pack('<H',pop));m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 pairs=sorted(set([(v,w) for v in (0,1,5,9,10,15,80,95,99,100) for w in (0,1,5,9,10,15,80,95,99,100)]+[(v,100) for v in range(256)]+[(100,v) for v in range(256)]))
 rows=[]
 for bgm,sound in pairs:
  m.mem_write(menu,bytes(0x7000));m.mem_write(root,bytes(0x1000));binds.clear()
  put(menu+0x2cc,1000);put(0x4f56cc,arena+0x70000)
  m.mem_write(0x4d9156,bytes([bgm,sound]));put(root+0x580,root)
  put(root+0x584,vms[ids[0]]+0x580)
  for index,i in enumerate(ids):
   vm=vms[i];m.mem_write(vm,bytes(0x1000));put(vm+0x18,0xabc00002);put(vm+0x540,i)
   m.mem_write(vm+0x4aa,struct.pack('<H',i));put(vm+0x580,vm)
   put(vm+0x584,vms[ids[index+1]]+0x580 if index+1<len(ids) else 0)
  put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x45b870,arena,count=20000);assert m.reg_read(UC_X86_REG_EIP)==arena,hex(m.reg_read(UC_X86_REG_EIP))
  assert len(binds)==12
  rows.append(dict(bgm=bgm,sound=sound,bindings=binds[:],visible=[[i,bool(get(vms[i]+0x18)&2)] for i in ids]))
 (ROOT/'artifacts/th14/title-options-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows),indent=2)+'\n')
 print(f'{len(rows)} retail title volume display cases')
if __name__=='__main__':main()
