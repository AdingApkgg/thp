"""TH14 original background ANM template/copy/update with real sprite binding."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-asset-anm-geometry';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 parser=importlib.import_module('th-anm-script-dump');m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in image.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,image.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x200000);vm=base+0x1000;resource=base+0x3000;sprites=base+0x10000;table=base+0x20000;code=base+0x30000;templates=base+0x60000;manager=base+0x80000;stack=base+0x1f0000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 m.mem_write(0x4854a0,b'\xc3');put(0x4db520,manager);put(0x4f56cc,manager);floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16)
 def run(entry,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,base,count=200000)
  except Exception as e:raise RuntimeError(f'entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
  assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 allocations={};requests=[];pool=base+0x100000
 m.mem_write(0x485540,b'\xc3')
 def allocator(machine,address,size,user):
  nonlocal pool
  n=get(machine.reg_read(UC_X86_REG_ESP)+4);assert 0<n<=0x10000,(n,hex(machine.reg_read(UC_X86_REG_EIP)));assert pool+n<base+0x1e0000
  m.mem_write(pool,bytes([0xcd])*n);allocations[pool]=n;requests.append(n);machine.reg_write(UC_X86_REG_EAX,pool);pool=(pool+n+15)&~15
 m.hook_add(UC_HOOK_CODE,allocator,begin=0x485540,end=0x485540)
 def geometry(p):
  pointer=get(p+0x5b4)
  if not pointer:return []
  assert pointer in allocations,hex(pointer)
  return list(struct.unpack('<'+'I'*(allocations[pointer]//4),m.mem_read(pointer,allocations[pointer])))
 offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
 def state(p,slot):
  pointer=get(p+0x2c);sprite=(pointer-sprites)//72 if pointer else -1;instruction=get(p+0x28)
  return [sprite&0xffffffff,get(p+0x18)&1,(get(p+0x18)>>25)&31,*[get(p+o) for o in offsets],(instruction-(code+slot*0x1000))&0xffffffff if instruction else 0xffffffff]
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());rows=[];resources=[];excluded=[]
 for stage in (4,7):
  name=f'st0{stage}wl.anm';raw=(Path(archive['extraction'])/name).read_bytes();expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name);assert sha(raw)==expected
  bodies=list(parser.scripts(raw));selected=[]
  for slot,_,body in bodies:
   at=0;ops=set()
   while at<len(body):
    op,length,_,_=struct.unpack_from('<hHhH',body,at);ops.add(op)
    if op==-1:break
    at+=length
   if ops&{508}:excluded.append(dict(name=name,slot=slot,opcodes=sorted(ops&{508})))
   else:selected.append(slot)
  if not selected:continue
  m.mem_write(resource,bytes(0x200));m.mem_write(resource,struct.pack('<H',(stage&1)+3));put(resource+0x120,table);put(resource+0x10c,templates);sprite_count=0
  for _,chunk in parser.chunks(raw):
   ns=struct.unpack_from('<H',chunk,4)[0];width,height=struct.unpack_from('<HH',chunk,10)
   for i in range(ns):
    off=struct.unpack_from('<I',chunk,64+i*4)[0];source,x,y,w,h=struct.unpack_from('<I4f',chunk,off);p=sprites+sprite_count*72;m.mem_write(p,bytes(72));floats(p+0x24,[f32(x/width),f32(y/height),f32(f32(x+w)/width),f32(f32(y+h)/height)]);floats(p+0x1c,[height,width]);floats(p+0x34,[h,w,1,1]);sprite_count+=1
  put(resource+0x108,sprite_count);put(resource+0x11c,sprites)
  for slot,_,body in bodies:assert len(body)<=0x1000;m.mem_write(code+slot*0x1000,body);put(table+slot*4,code+slot*0x1000)
  resources.append(dict(name=name,sha256=expected,sprites=sprite_count,scripts=len(bodies),selected=selected))
  for rate in (.3,.5,.99,1,1.01,1.25):
   floats(0x4d8f58,[rate]);m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0));m.mem_write(templates,bytes(len(bodies)*0x5cc))
   for slot,_,_ in bodies:
    p=templates+slot*0x5cc;run(0x46f3e0,resource,(p,slot))
    for o,v in [(0x548,-2),(0x54c,-1),(0x550,0xbf800000),(0x55c,-2),(0x560,-1),(0x564,0xbf800000)]:put(p+o,v)
    assert run(0x46fe50,p)==0
   template_rng=list(struct.unpack('<8H',m.mem_read(0x4db508,16)))
   for slot in selected:
    pool=base+0x100000;allocations.clear();requests.clear();m.mem_write(vm,bytes(0x5cc));m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0));run(0x40af00,resource,(vm,slot));bound=state(vm,slot);bound_geometry=geometry(vm);timeline=[]
    for frame in range(1200):
     status=run(0x46fe50,vm);timeline.append(dict(status=status,state=state(vm,slot),rng=list(struct.unpack('<4I',m.mem_read(0x4db508,16))),geometry=geometry(vm)))
     if status:break
    rows.append(dict(name=name,slot=slot,rate=rate,template=state(templates+slot*0x5cc,slot),templateRng=template_rng,bound=bound,boundGeometry=bound_geometry,allocations=list(requests),timeline=timeline))
  print('native background ANM',name,len(selected),flush=True)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,resources=resources,excluded=excluded,rows=rows,offsets=offsets,executableSha256=sha(image.data),toolSha256=sha(Path(__file__).read_bytes()),parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()),scope='Original st04/07 background ANM scripts with609/610 geometry factories, controlled485540 allocation returning distinct poison-filled blocks, excluding508 owner effects. Whole46f3e0 binding, real memset, negative-time template initialization, whole40af00 copy and whole46fe50 for1200 updates or termination; whole46f1e0 sprite binding uses descriptor UV/size reconstructed from original ANM chunks. Six rates, selected raw VM fields and RNG words. Real original resource loader/sprite descriptor construction, child effects, rendering/world/HAL/audio are outside this proof; excluded scripts explicitly listed, no complete original ANM equivalence.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS native asset ANM',len(rows),sum(len(r['timeline']) for r in rows))
if __name__=='__main__':main()
