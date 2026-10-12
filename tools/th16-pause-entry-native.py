"""Own pause entry/capture prefix and418fe0 overlay factory with controlled boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000)
 menu,control,hud,text,front,vm,stack,ret=(0x70000000+n for n in (0x1000,0x5000,0x6000,0x8000,0x9000,0xa000,0x3d000,0x3e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bindings=[];sounds=[];factory=False;capture_prefix=False;program=0;ticks=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);ecx=machine.reg_read(UC_X86_REG_ECX)
  if a==0x418fe0 and not factory:
   out=get(sp+4);bindings.append([0 if ecx==text else 5,get(sp+8)]);put(out,100+len(bindings));machine.reg_write(UC_X86_REG_EAX,out)
  elif a==0x43ef20:
   if not capture_prefix:bindings.append([0,52])
  elif a==0x45e150:sounds.append(get(sp+4))
  elif a in (0x45e330,0x46efa0):machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x46f600:machine.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x407b20:put(vm+0x18,0);put(vm+0x534,0x80000);put(vm+0x51c,77)
  elif a==0x45f980:
   ticks.append([get(vm+0x534)&0x400,*[get(vm+o) for o in (0x5e0,0x5e4,0x5e8,0x40)]]);put(vm+0x18,35 if program else 0);machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x46e940:put(get(sp+4),200);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
 for a,cleanup in ((0x42dbc0,0),(0x42e4d0,0),(0x45e150,8),(0x45ed00,12),(0x45e330,0),(0x46f0b0,8),(0x46f1c0,4),(0x43ef20,0),(0x46efa0,4),(0x46f600,0),(0x407b20,8),(0x45f980,0),(0x46e940,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 original=bytes(m.mem_read(0x418fe0,3));m.mem_write(0x418fe0,b'\xc2\x0c\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x418fe0,end=0x418fe0)
 def reset():
  m.mem_write(0x70000000,bytes(0x3c000));bindings.clear();sounds.clear();ticks.clear()
  for p,v in ((0x4a6ef4,menu),(0x4a6dd4,control),(0x4a6dcc,hud),(0x4c17f8,text),(hud+0x2d8,front),(0x4a5bec,0x20),(0x4a5788,0x3f800000),(0x4d9d90,1)):put(p,v)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu)
 entries=[]
 for replay in (0,1):
  reset();put(control+0xac,replay);m.emu_start(0x43f0f0,ret,count=10000);assert m.reg_read(UC_X86_REG_EIP)==ret
  entries.append(dict(kind='pause',replay=replay,bindings=list(bindings),sounds=list(sounds),state=[get(menu+0x1ec),get(menu+0x1f4)]))
 reset();m.emu_start(0x43f350,0x43f431,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x43f431
 entries.append(dict(kind='game_over',replay=0,bindings=list(bindings),sounds=list(sounds),state=[get(menu+0x1ec),get(menu+0x1f4)]))
 # Run actual capture-request prefix, stopping before GPU/sprite access.
 capture_prefix=True;m.mem_write(0x43ef20,bytes.fromhex('55 8b ec'));m.ctl_remove_cache(0x43ef20,0x43ef60)
 capture=[]
 for old in (0,123):
  reset();put(menu+0x1e8,old);m.emu_start(0x43ef20,0x43ef60,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x43ef60
  capture.append(dict(old=old,bindings=list(bindings)))
 factory=True;m.mem_write(0x418fe0,original);m.ctl_remove_cache(0x418fe0,0x419090);rows=[]
 for script in (52,156,158):
  for program in (0,1):
   reset();m.reg_write(UC_X86_REG_ECX,text if script==52 else front);put(stack+4,menu);put(stack+8,script);put(stack+12,0)
   m.emu_start(0x418fe0,ret,count=10000);assert m.reg_read(UC_X86_REG_EIP)==ret
   rows.append(dict(script=script,program=program,tick=ticks[0],output=[get(vm+0x18),get(vm+0x534)&0x400,*[get(vm+o) for o in (0x5e0,0x5e4,0x5e8,0x40,0x51c)]]))
 (ROOT/'artifacts/th16/pause-entry-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,capture=capture,factories=rows),indent=2)+'\n',encoding='utf-8');print('3 own pause/end entry paths, 2 capture prefixes and 6 overlay factory bodies')
if __name__=='__main__':main()
