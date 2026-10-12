"""TH14 original background ANM template/copy/update with real sprite binding."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-animation-update-order';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 parser=importlib.import_module('th-anm-script-dump');m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in image.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,image.data[raw:raw+n])
 base=0x70000000;m.mem_map(0,4096);m.mem_map(base,0x200000);vm=base+0x1000;resource=base+0x3000;sprites=base+0x10000;table=base+0x20000;code=base+0x30000;templates=base+0x60000;manager=base+0x80000;stack=base+0x1f0000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 m.mem_write(0x4854a0,b'\xc3');put(0x4db520,manager);put(0x4f56cc,manager);floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16)
 def run(entry,owner,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,base,count=200000)
  except Exception as e:raise RuntimeError(f'entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
  assert m.reg_read(UC_X86_REG_EIP)==base;return m.reg_read(UC_X86_REG_EAX)
 offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
 def state(p,slot):
  pointer=get(p+0x2c);sprite=(pointer-sprites)//72 if pointer else -1;instruction=get(p+0x28)
  return [sprite&0xffffffff,get(p+0x18)&1,(get(p+0x18)>>25)&31,*[get(p+o) for o in offsets],(instruction-(code+slot*0x1000))&0xffffffff if instruction else 0xffffffff]

 dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll');assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 for _,b,size,raw,n in dll.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,dll.data[raw:raw+n])
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,0,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)]
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128)
  if name=='D3DXVec3Normalize':ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];put(0x4b12b8,dll.image_base+dll.u32(functions+ordinal*4))
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());name='st01wl.anm';raw=(Path(archive['extraction'])/name).read_bytes();expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name);assert sha(raw)==expected;bodies=list(parser.scripts(raw))
 m.mem_write(resource,bytes(0x200));m.mem_write(resource,struct.pack('<H',3));put(resource+0x120,table);put(resource+0x10c,templates);sprite_count=0
 for _,chunk in parser.chunks(raw):
  ns=struct.unpack_from('<H',chunk,4)[0];width,height=struct.unpack_from('<HH',chunk,10)
  for i in range(ns):
   off=struct.unpack_from('<I',chunk,64+i*4)[0];source,x,y,w,h=struct.unpack_from('<I4f',chunk,off);p=sprites+sprite_count*72;m.mem_write(p,bytes(72));floats(p+0x24,[f32(x/width),f32(y/height),f32(f32(x+w)/width),f32(f32(y+h)/height)]);floats(p+0x1c,[height,width]);floats(p+0x34,[h,w,1,1]);sprite_count+=1
 put(resource+0x108,sprite_count);put(resource+0x11c,sprites)
 for slot,_,body in bodies:assert len(body)<=0x1000;m.mem_write(code+slot*0x1000,body);put(table+slot*4,code+slot*0x1000)
 stage=base+0x90000;std=base+0xa0000;header=base+0xb0000;rows=[];m.mem_write(std,struct.pack('<ihh',0,0,8));m.mem_write(header,bytes(16))
 def stage_state():return [get(stage+o) for o in (0x4240,0x38,0x3c,0x40,0x3094,0x3098)]+[get(0x4d9514+i*4) for i in range(9)]
 for rate in (.3,.5,.99,1,1.01,1.25):
  floats(0x4d8f58,[rate]);m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0));m.mem_write(templates,bytes(len(bodies)*0x5cc))
  for slot,_,_ in bodies:
   p=templates+slot*0x5cc;run(0x46f3e0,resource,(p,slot))
   for o,v in [(0x548,-2),(0x54c,-1),(0x550,0xbf800000),(0x55c,-2),(0x560,-1),(0x564,0xbf800000)]:put(p+o,v)
   assert run(0x46fe50,p)==0
  for flags in (0,4,8):
   for fade in (29,30,59,60):
    m.mem_write(stage,bytes(0x4500));put(stage+0x10,header);put(stage+0x1c,std);put(stage+0x4c,std);put(stage+0x38,-1);put(stage+0x44,0x4d8f58);put(stage+0x48,1);put(stage+0x4224,flags);put(stage+0x422c,fade);put(stage+0x204,resource);floats(stage+0x4274,[0,0,-600,0,300,600,0,1,0]);floats(stage+0x42c8,[.5235987901687622]);m.mem_write(0x4d9514,bytes(0x12c));m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0))
    for i in range(8):run(0x40af00,resource,(stage+0x20c+i*0x5cc,0))
    timeline=[]
    for frame in range(16):
     assert run(0x40d980,stage)==1;timeline.append(dict(stage=stage_state(),vms=[state(stage+0x20c+i*0x5cc,0) for i in range(8)],rng=list(struct.unpack('<4I',m.mem_read(0x4db508,16)))))
    rows.append(dict(rate=rate,flags=flags,fade=fade,timeline=timeline))
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,rows=rows,resource=dict(name=name,sha256=expected),executableSha256=sha(image.data),dllSha256=sha(dll.data),toolSha256=sha(Path(__file__).read_bytes()),parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()),scope='Whole original40d980 Stage update, whole46fe50 embedded ANM, real32 D3DXVec3Normalize, original st01wl script0 templates and copy. Eight controlled live embedded VMs, zero ordinary objects, STD stop instruction, six rates and flags0/4/8 with fade29/30/59/60,16 updates each. Selected51 VM words plus Stage clocks/tint and published9 camera words, RNG. Zeroed FS/SEH scratch page mapped. Resource descriptors reconstructed, Stage setup and frozen fade clock controlled; no draw, complete original construction/world/audio/HAL proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS native whole Stage update',len(rows),sum(len(r['timeline']) for r in rows))
if __name__=='__main__':main()
