"""Execute TH14's resource/chunk/descriptor loader; control file and GPU services."""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/anm-resource-loader'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 parser=importlib.import_module('th-anm-script-dump')
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in image.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,image.data[raw:raw+n])
 base=0x70000000;manager=0x71000000;heap_base=0x73000000
 m.mem_map(0,4096);m.mem_map(base,0x100000);m.mem_map(manager,0x1000000);m.mem_map(heap_base,0x4000000)
 stack=base+0xf0000;path=base+0x2000;desc_stub=base+0x1000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 def string(p):
  b=bytearray()
  while len(b)<512:
   c=m.mem_read(p+len(b),1)[0]
   if not c:return b.decode('ascii')
   b.append(c)
  raise AssertionError('unterminated filename')
 def ret(value=0,argc=0):
  sp=m.reg_read(UC_X86_REG_ESP);target=get(sp)
  m.reg_write(UC_X86_REG_EAX,value&0xffffffff);m.reg_write(UC_X86_REG_ESP,sp+4+argc*4);m.reg_write(UC_X86_REG_EIP,target)
 current={};allocations=[];reads=[];uploads=[];descriptions=[];heap=heap_base
 def allocate(n):
  nonlocal heap
  assert 0<n<=0x1000000
  p=heap;heap=(heap+n+15)&~15;assert heap<=heap_base+0x4000000
  m.mem_write(p,b'\xcd'*n);allocations.append(n);return p
 def malloc(m,address,size,user):ret(allocate(get(m.reg_read(UC_X86_REG_ESP)+4)))
 def noop(m,address,size,user):ret()
 def cookie(m,address,size,user):ret(m.reg_read(UC_X86_REG_EAX))
 def filename(m,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);name=string(get(sp+12));assert name==current['name']
  m.mem_write(get(sp+4),(name+'\0').encode());ret(len(name))
 def file_read(m,address,size,user):
  name=string(m.reg_read(UC_X86_REG_ECX));assert name==current['name'],name
  sp=m.reg_read(UC_X86_REG_ESP);assert get(sp+4)==0
  p=allocate(len(current['raw']));m.mem_write(p,current['raw']);out=m.reg_read(UC_X86_REG_EDX)
  if out:put(out,len(current['raw']))
  reads.append(name);ret(p,1)
 def upload(m,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);entry=get(sp+4);chunk=current['chunk']
  assert address==0x47cb70,'unexpected nonembedded texture'
  assert get(sp+8)==current['source']+current['offset']+struct.unpack_from('<I',chunk,28)[0]
  width,height=struct.unpack_from('<HH',chunk,10)
  texture=allocate(16);table=allocate(0x60);m.mem_write(table,bytes(0x60));put(texture,table);put(table+0x44,desc_stub)
  current['textures'][texture]=(width,height);put(entry,texture)
  uploads.append(dict(chunk=current['index'],width=width,height=height,format=get(sp+12)))
  ret(0,5)
 def describe(m,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);texture=get(sp+4);assert get(sp+8)==0
  width,height=current['textures'][texture];p=get(sp+12);m.mem_write(p,bytes(32));put(p+24,width);put(p+28,height)
  descriptions.append([width,height]);ret(0,3)
 for addr,fn in [(0x485540,malloc),(0x4854af,malloc),(0x47ff50,noop),(0x4854a0,cookie),(0x485ddf,filename),(0x402b00,file_read),(0x47cb70,upload),(desc_stub,describe)]:m.hook_add(UC_HOOK_CODE,fn,begin=addr,end=addr)
 put(0x4f56cc,manager);put(0x4db520,manager);put(0x4f7a64,640);put(0x4f7a68,480);put(0x4d9684,0x180)
 def run(entry,owner=0,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner)
  m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,base,count=5000000)
  except Exception as e:raise RuntimeError(f'entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
  assert m.reg_read(UC_X86_REG_EIP)==base
  return m.reg_read(UC_X86_REG_EAX)
 archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());rows=[]
 offsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
 def vm_state(p,resource,slot):
  sprite=get(p+0x2c);instruction=get(p+0x28);origin=get(get(resource+0x120)+slot*4)
  return [((sprite-get(resource+0x11c))//72)&0xffffffff if sprite else 0xffffffff,get(p+0x18)&1,(get(p+0x18)>>25)&31,*[get(p+o) for o in offsets],(instruction-origin)&0xffffffff if instruction else 0xffffffff]
 for stage,rate in [(stage,rate) for stage in range(1,8) for rate in (.3,.5,.99,1,1.01,1.25)]:
  name=f'st0{stage}wl.anm';raw=(Path(archive['extraction'])/name).read_bytes()
  expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name);assert sha(raw)==expected
  heap=heap_base;allocations.clear();reads.clear();uploads.clear();descriptions.clear();m.mem_write(manager+0xbc7b0c,bytes(64))
  current.clear();current.update(name=name,raw=raw,textures={});m.mem_write(path,(name+'\0').encode());m.mem_write(0x4d8f58,struct.pack('<f',rate));m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0))
  resource=run(0x47d090,manager,((stage&1)+3,path));assert resource and get(manager+0xbc7b0c+((stage&1)+3)*4)==resource
  current['source']=get(resource+0x108);assert bytes(m.mem_read(current['source'],len(raw)))==raw
  sprite=script=index=0;scheduling=[]
  chunks=list(parser.chunks(raw))
  assert get(resource+0x128)==1
  for offset,chunk in chunks:
   assert chunk[32] and chunk[struct.unpack_from('<I',chunk,16)[0]]!=ord('@')
   current.update(chunk=chunk,offset=offset,index=index)
   before=get(resource+0x128);assert before==index+1
   assert run(0x47d230,args=(resource,))==resource
   after=get(resource+0x128);assert after==(index+2 if index+1<len(chunks) else 0)
   scheduling.append([before,after])
   sprite+=struct.unpack_from('<H',chunk,4)[0];script+=struct.unpack_from('<H',chunk,6)[0];index+=1
  assert [get(resource+o) for o in [0x110,0x114,0x118]]==[index,script,sprite]
  sprite_rows=[]
  for i in range(sprite):
   p=get(resource+0x11c)+i*72
   words=list(struct.unpack('<18I',m.mem_read(p,72)));texture=(words[2]-get(resource+0x124))//24
   assert 0<=texture<index and words[2]==get(resource+0x124)+texture*24
   sprite_rows.append(dict(index=i,texture=texture,words=words))
  script_offsets=[]
  for base_offset,chunk in parser.chunks(raw):
   ns,nc=struct.unpack_from('<HH',chunk,4)
   script_offsets.extend(base_offset+struct.unpack_from('<I',chunk,64+ns*4+i*8+4)[0] for i in range(nc))
  scripts=[];templates=[]
  for slot,source_id,body in parser.scripts(raw):
   offset=script_offsets[slot]
   p=get(get(resource+0x120)+slot*4);assert p-current['source']==offset,(name,slot,offset,hex(p),hex(current['source']))
   assert bytes(m.mem_read(p,len(body)))==body
   scripts.append(dict(slot=slot,source_id=source_id,offset=offset,bytes=len(body),sha256=sha(body)))
   templates.append(vm_state(get(resource+0x10c)+slot*0x5cc,resource,slot))
  rows.append(dict(name=name,rate=rate,sha256=expected,chunks=index,sprites=sprite_rows,scripts=scripts,templates=templates,templateRng=list(struct.unpack('<4I',m.mem_read(0x4db508,16))),scheduling=scheduling,allocations=list(allocations),fileReads=list(reads),uploads=list(uploads),descriptions=list(descriptions)))
  print('original progressive resource loader',name,rate,index,sprite,script,flush=True)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,rows=rows,executableSha256=sha(image.data),toolSha256=sha(Path(__file__).read_bytes()),parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()),reference='reference/th11-eagler/th11_web/tests/cpp/anm-oracle.mjs',scope='Actual original47d090 wrapper with controlled0x180 bypass of OS wait,47cff0/47ce40 resource allocation and file/chunk parsing,47d130 preload,47d230 progressive chunk loading and final template initialization,47d420 texture/sprite/script table construction and47d9e0 descriptor arithmetic, actual40cc90 VM constructor/46f3e0 binding/negative-time46fe50. Six rates, progress counter per actual chunk and completion, selected51 template words and RNG. Exact original background ANM bytes supplied by controlled402b00 file service, separate poisoned heap allocations, actual48f980 memset. Embedded texture GPU creation and GetLevelDesc return original ANM header dimensions; filename formatting, logging and cookie check are controlled. Whole descriptor bytes retain pointer/reserved values for audit; portable comparison selects declared fields, excluding those bytes. Original progressive routine called explicitly without OS thread scheduling; no actual D3D resource upload, filesystem/DAT I/O, rendering/HAL/audio or complete1:1 claim.')
 (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
