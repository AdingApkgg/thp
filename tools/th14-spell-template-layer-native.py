"""Original three inline spell-title factories; binding/update/registry are controlled."""
from pathlib import Path
import hashlib,importlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  a=b&~4095;m.mem_map(a,((b+size+4095)&~4095)-a);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);resource=base+0x1000;vm=base+0x3000;spell=base+0x5000;stack=base+0x1f000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];layer=0
 def hook(u,a,n,x):
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==0x47fcb0:u.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:put(vm+0x24,layer)
  elif a==0x47e890:put(get(sp+4),73);u.reg_write(UC_X86_REG_EAX,get(sp+4))
 for a,cleanup in [(0x47fcb0,0),(0x40af00,8),(0x46fe50,0),(0x47e890,8)]:
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup)if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[];m.mem_write(0x4f5815,b'\0')
 for layer in [0,7,13,27]:
  for slot,start,end in [(0,0x41cd07,0x41cd8c),(1,0x41cdaf,0x41ce34),(2,0x41ce5c,0x41cee1)]:
   m.mem_write(vm,bytes(0x700));put(stack+0x10,resource);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ESI,resource);m.reg_write(UC_X86_REG_EDI,spell);m.emu_start(start,end,count=1000);assert m.reg_read(UC_X86_REG_EIP)==end
   rows.append(dict(slot=slot,inputLayer=layer,actualLayer=get(vm+0x24)))
 out=ROOT/'artifacts/th14/spell-template-layer-check';out.mkdir(parents=True,exist_ok=True);(out/'native.json').write_text(json.dumps(dict(originalExecutableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,controlledBoundaries=['allocation','template binding','first ANM update','registry publication']),indent=2)+'\n');print(json.dumps(dict(cases=len(rows))))
if __name__=='__main__':main()
