"""Retail ANM413/414 flags and inline HUD95 factory, with explicit unit inputs."""
from pathlib import Path
import hashlib,importlib,json,struct,itertools
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,table,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  a=b&~4095;m.mem_map(a,((b+size+4095)&~4095)-a);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x20000);vm=base+0x1000;code=base+0x2000;resource=base+0x3000;game=base+0x5000;stack=base+0x1f000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];rows=[]
 for op,mode_bits,duration,mode in itertools.product((413,414),(0,0x20000,0x40000,0x60000),(-1,0,1,40),(0,7,31,255)):
  flags=0xa4000007|mode_bits;args=[duration,mode,23,67,89]if op==413 else[duration,mode,123];m.mem_write(vm,bytes(0x700));put(vm+0x18,flags);put(vm+0x534,0xc0123456);put(vm+0x538,0x9a6587ab);put(0x4d8f58,0x3f800000);m.mem_write(code,struct.pack('<hHhH',op,8+len(args)*4,0,0)+struct.pack('<'+'i'*len(args),*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack);m.reg_write(UC_X86_REG_EDI,vm);m.reg_write(UC_X86_REG_EBX,code);m.emu_start(table[op],0x47007e,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x47007e;rows.append(dict(op=op,initialFlags=flags,duration=duration,mode=mode,flags=get(vm+0x18)))
 layer=0
 def boundary(u,a,n,user):
  if a==0x47fcb0:u.reg_write(UC_X86_REG_EAX,vm)
  else:put(vm+0x24,layer)
 for a,cleanup in [(0x47fcb0,0),(0x40af00,8)]:m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup)if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 hud=[];m.mem_write(0x4f5815,b'\0')
 for layer in (0,7,22,27):
  m.mem_write(vm,bytes(0x700));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.reg_write(UC_X86_REG_EBX,resource);m.emu_start(0x4348ec,0x434943,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x434943;hud.append(dict(inputLayer=layer,actualLayer=get(vm+0x24)))
 out=ROOT/'artifacts/th14/final-visual-state-check';out.mkdir(parents=True,exist_ok=True);(out/'native.json').write_text(json.dumps(dict(originalExecutableSha256=hashlib.sha256(img.data).hexdigest(),secondary=rows,hud=hud,controlledVmInputs=True,hudAllocationAndBindingControlled=True),indent=2)+'\n');print(json.dumps(dict(secondaryCases=len(rows),hudCases=len(hud))))
if __name__=='__main__':main()
