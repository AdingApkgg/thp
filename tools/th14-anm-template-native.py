"""Retail resource template initialization and40af00 copy, effect.anm21.

Uses the original script bytes and whole46f3e0/46fe50/40af00 entries.
Sprite binding and memset are controlled service boundaries.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);vm=base+0x1000;dst=base+0x2000;resource=base+0x3000;code=base+0x4000;table=base+0x5000;stack=base+0xf0000
 parent=base+0x7000;handle=base+0x8000
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());source=Path(archive['extraction'])/'effect.anm'
 body=next(b for slot,_,b in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes()) if slot==21)
 m.mem_write(code,body);sprite_calls=[];raw_status=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:
   p,v,size=get(sp+4),get(sp+8),get(sp+12);m.mem_write(p,bytes([v&255])*size);uc.reg_write(UC_X86_REG_EAX,p);pop=0
  elif a==0x46f1e0:
   sprite_calls.append(get(sp+8));uc.reg_write(UC_X86_REG_EAX,0);pop=8
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,dst);pop=0
  elif a in (0x47e890,0x47e950,0x47e9f0,0x47eab0):
   put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x46f63c:raw_status.append(uc.reg_read(UC_X86_REG_EAX));return
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x48f980,0x46f1e0,0x47fcb0,0x47e890,0x47e950,0x47e9f0,0x47eab0,0x46f63c):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 m.mem_write(0x4854a0,b'\xc3');put(0x4db520,base+0x6000);put(0x4f56cc,base+0x6000);put(0x4d8f58,0x3f800000);m.mem_write(resource,bytes(0x200));m.mem_write(resource,struct.pack('<H',8));put(resource+0x120,table);put(table+21*4,code)
 def run(address,owner,args=(),stop=None):
  m.mem_write(stack,struct.pack('<'+str(len(args)+1)+'I',base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,0);m.reg_write(UC_X86_REG_ECX,owner)
  m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(address,stop or base,count=100000)
  except Exception as error:raise RuntimeError(f'entry{address:x} pc{m.reg_read(UC_X86_REG_EIP):x}') from error
  assert m.reg_read(UC_X86_REG_EIP)==(stop or base);return m.reg_read(UC_X86_REG_EAX)
 # Canonical observations have corresponding native fields here.
 offsets=[0x4ac,0x4b0,0x24,0x534,0x54c,0x550,0x3c,0x40,0x44,0x60,0x64,0x4e0,0x4e4,0x4e8]
 def state(p):return [get(p+o) for o in offsets]+[get(p+0x28)-code]
 rows=[]
 for seed in (0,1,904,65535):
  for calls in (0,97,0xfffffffc):
   m.mem_write(vm,bytes(0x700));m.mem_write(0x4db508,struct.pack('<HHI',seed,0,calls));sprite_calls.clear();run(0x46f3e0,resource,(vm,21))
   for o,v in [(0x548,0xfffffffe),(0x54c,0xffffffff),(0x550,0xbf800000),(0x55c,0xfffffffe),(0x560,0xffffffff),(0x564,0xbf800000)]:put(vm+o,v)
   status=run(0x46fe50,vm);assert status==0;template=state(vm);rng=list(struct.unpack('<HHI',m.mem_read(0x4db508,8)));copies=[]
   #40af00 indexes slot21 in the template array.
   put(resource+0x10c,vm-21*0x5cc)
   for creation in range(3):
    m.mem_write(dst,bytes(0x700));m.mem_write(dst+0x59c,struct.pack('<fff',320,400,-8));run(0x40af00,resource,(dst,21));bound=state(dst);status=run(0x46fe50,dst)
    copies.append(dict(bound=bound,updated=state(dst),status=status,origin=list(struct.unpack('<3I',m.mem_read(dst+0x59c,12))),rng=list(struct.unpack('<HHI',m.mem_read(0x4db508,8)))))
   factories=[]
   for detached,flags in [(False,0),(False,4),(False,6),(True,0)]:
    m.mem_write(dst,bytes(0x700));m.mem_write(parent,bytes(0x700));put(parent+0x24,27);put(parent+0x1c,0x1000000);put(parent+0x580,parent)
    m.mem_write(parent+0x59c,struct.pack('<fff',320,400,-8));m.mem_write(parent+0x48,struct.pack('<fff',.25,-.5,.75));m.mem_write(parent+0x3c,struct.pack('<fff',12,-34,56))
    run(0x47efc0 if detached else 0x47ee90,resource,(handle,21,parent,flags))
    factories.append(dict(detached=detached,flags=flags,state=state(dst),flags2=get(dst+0x1c),parent=get(dst+0x594)!=0,origin=list(struct.unpack('<3I',m.mem_read(dst+0x59c,12))),rotation=list(struct.unpack('<3I',m.mem_read(dst+0x48,12))),childPosition=list(struct.unpack('<3I',m.mem_read(dst+0x4ec,12))),rng=list(struct.unpack('<HHI',m.mem_read(0x4db508,8)))))
   m.mem_write(dst,bytes(0x700));m.mem_write(dst+0x59c,struct.pack('<fff',320,400,-8));run(0x40cc90,dst);raw_status.clear();run(0x46f520,resource,(dst,21),0x46f635);raw_bound=state(dst)
   m.emu_start(0x46f635,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
   raw=dict(bound=raw_bound,updated=state(dst),status=raw_status[-1],rng=list(struct.unpack('<HHI',m.mem_read(0x4db508,8))))
   rows.append(dict(seed=seed,calls=calls,template=template,rng=rng,copies=copies,factories=factories,raw=raw,spriteCalls=sprite_calls[:]))
 out=dict(passed=True,rows=rows,offsets=offsets,scriptHex=body.hex(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Original effect.anm21: whole46f3e0 binding, resource-loader clock-1 setup, whole46fe50 negative-time initialization, three whole40af00 copies and first updates; whole46f520 raw binding observed before and after its real first interpreter update; whole47ee90 attached/47efc0 detached factories compare layer/flags2/live-parent/origin/rotation/child-position. Selected variables/colors/layer/transforms/random parameters/instruction/clocks and full RNG words. Sprite binding, memset, pool allocation and registry service controlled; geometry, arbitrary resources and GPU output excluded.')
 (ROOT/'artifacts/th14/anm-template-native.json').write_text(json.dumps(out,indent=2)+'\n');print(f'PASS {len(rows)} native templates and {len(rows)*3} copies')
if __name__=='__main__':main()
