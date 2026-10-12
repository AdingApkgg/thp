"""Whole retail interpreter on actual dialogue-panel child scripts."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);template=base+0x1000;vm=base+0x2000;resource=base+0x3000;code=base+0x4000;table=base+0x6000;stack=base+0xf0000
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());source=Path(archive['extraction'])/'front.anm';bodies={s:b for s,_,b in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes()) if s in range(168,216)}
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 sprite=-1
 def hook(uc,a,n,u):
  nonlocal sprite
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:dst=get(sp+4);m.mem_write(dst,bytes([get(sp+8)&255])*get(sp+12));uc.reg_write(UC_X86_REG_EAX,dst);pop=0
  elif a==0x46f1e0:sprite=get(sp+8);uc.reg_write(UC_X86_REG_EAX,0);pop=8
  elif a==0x4854a0:pop=0
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x46f1e0,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(0x4db520,base+0x8000);put(0x4f56cc,base+0x8000);put(resource+0x120,table)
 def run(address,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=(0x534,0x538,0x24,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4a0,0x4bc,0x4c0,0x78,0x7c)
 def state():return [sprite&0xffffffff,*[get(vm+o) for o in offsets],get(vm+0x528)&0xffff,get(vm+0x1c)&0xa00,get(vm+0x18)&1,get(vm+0x28)-code if get(vm+0x28) else 0xffffffff]
 rows=[]
 for slot,rate,width in itertools.product(range(168,216),(.5,1.,1.25),(32.,128.,384.)):
  m.mem_write(code,bodies[slot]);m.mem_write(template,bytes(0x700));m.mem_write(vm,bytes(0x700));put(table+slot*4,code);m.mem_write(0x4d8f58,struct.pack('<f',rate));sprite=-1;run(0x46f3e0,resource,(template,slot))
  for o,v in ((0x548,-2),(0x54c,-1),(0x550,0xbf800000)):put(template+o,v)
  assert run(0x46fe50,template)==0;put(resource+0x10c,(template-slot*0x5cc)&0xffffffff);run(0x40af00,resource,(vm,slot));put(vm+0x1c,get(vm+0x1c)|0x200);assert run(0x46fe50,vm)==0;m.mem_write(vm+0x4bc,struct.pack('<f',width))
  frames=[];initial=state()
  for frame in range(160):
   label={12:2,45:3,60:8,90:1}.get(frame)
   if label is not None:put(vm+0x4a0,label)
   status=run(0x46fe50,vm);frames.append(dict(status=status,state=state()))
   if status:break
  rows.append(dict(input=[slot,rate,width],initial=initial,frames=frames))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows,offsets=offsets,scope='Actual front.anm168..215 panel children, whole46f3e0 template bind, loader clock-1/full46fe50, whole40af00 copy/first update, post-create variable10004 widths, full interpreter per tick with labels2/3/8/1. Sprite binding, memset and security-cookie boundaries controlled. Standalone child VMs: no original root allocation/parent linking, sprite/GPU or full Dialogue/world execution.')
 (ROOT/'artifacts/th14/dialogue-panel-animation-native.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native panel animations',len(rows),sum(len(r['frames']) for r in rows))
if __name__=='__main__':main()
