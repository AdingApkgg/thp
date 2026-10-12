"""Full retail 46fe50 on Sakuya B scripts 20, 21, 22.
Sprite binding, script-21 child delivery and security cookie are boundaries.
The child script 22 is measured independently with the same full interpreter.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main(character=2,slots=(20,21,22),name='sakuya-b',interrupts=None,extra_offsets=()):
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);source=ROOT/f'artifacts/archive-differential/th14-bBPoO0/pl{character:02}.anm'
 bodies={slot:body for slot,_,body in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes())}
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
 ret,vm,code,stack=0x70000000,0x70001000,0x70003000,0x7001f000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 put(0x4db520,ret)
 sprite=-1;children=[]
 def sink(machine,a,size,user):
  nonlocal sprite
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x46f1e0:sprite=get(sp+8)
  elif a==0x47ee90:children.append(get(sp+8));m.reg_write(UC_X86_REG_EAX,0)
  elif a==0x485540:m.reg_write(UC_X86_REG_EAX,ret+0x30000)
 for a,cleanup in ((0x4854a0,0),(0x46f1e0,8),(0x47ee90,16),(0x485540,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 offsets=(0x534,0x24,0x1c,0x18,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x68,0x6c)+extra_offsets
 rows=[]
 for slot in slots:
  for rate in (.5,1,1.25):
   m.mem_write(vm,bytes(0x1000));m.mem_write(code,bodies[slot]);sprite=-1;children.clear()
   for off,v in ((0x18,6),(0x1c,0x200),(0x28,code),(0x38,code),(0x534,0xffffffff),(0x548,-999999),(0x554,0x4d8f58),(0x558,1),(0x60,0x3f800000),(0x64,0x3f800000),(0x68,0x3f800000),(0x6c,0x3f800000)):put(vm+off,v)
   m.mem_write(0x4d8f58,struct.pack('<f',rate));frames=[]
   interrupt_frame=interrupts.get(slot,-1) if interrupts else -1
   for frame in range(700 if interrupts else 300):
    if frame==interrupt_frame:put(vm+0x4a0,1)
    put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm)
    m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    try:m.emu_start(0x46fe50,ret,count=100000)
    except Exception as e:raise RuntimeError(f'slot {slot} rate {rate} frame {frame} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
    assert m.reg_read(UC_X86_REG_EIP)==ret
    status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(status=status,state=[sprite,*[get(vm+o)&1 if o==0x18 else get(vm+o) for o in offsets]]))
    if status:break
   rows.append(dict(slot=slot,rate=rate,children=children[:],interruptFrame=interrupt_frame,frames=frames))
 out=ROOT/f'artifacts/th14/{name}-anm-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf8')
 print(f'{sum(len(r["frames"]) for r in rows)} {name} native ANM frames.')
if __name__=='__main__':main()
