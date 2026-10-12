"""Shared controlled host services for the actual TH14 ANM resource loader.
The caller supplies an emulator with the pinned executable already mapped.
"""
import struct,importlib
from types import SimpleNamespace
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def install(m):
 base=0x70000000;manager=0x71000000;heap_base=0x73000000

 for address,size in [(0,4096),(base,0x100000),(manager,0x1000000),(heap_base,0x4000000)]:
  if not any(lo<=address and hi+1>=address+size for lo,hi,_ in m.mem_regions()):m.mem_map(address,size)
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
 def malloc(m,address,size,user):
  if current.get('loading',False):ret(allocate(get(m.reg_read(UC_X86_REG_ESP)+4)))
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
 put(0x4f56cc,manager);put(0x4db520,manager);put(0x4f7a64,640);put(0x4f7a68,480)
 def run(entry,owner=0,args=()):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),base,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner)
  m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,base,count=5000000)
  except Exception as e:raise RuntimeError(f'entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
  assert m.reg_read(UC_X86_REG_EIP)==base
  return m.reg_read(UC_X86_REG_EAX)
 def load(name,raw,file,rate):
  nonlocal heap
  heap=heap_base;allocations.clear();reads.clear();uploads.clear();descriptions.clear()
  m.mem_write(manager+0xbc7b0c,bytes(0x1a*4));current.clear();current.update(name=name,raw=raw,textures={},loading=True)
  m.mem_write(path,(name+'\0').encode());m.mem_write(0x4d8f58,struct.pack('<f',rate));m.mem_write(0x4db508,struct.pack('<HHIHHI',12345,0,0,54321,0,0))
  control=get(0x4d9684);put(0x4d9684,0x180)
  resource=run(0x47d090,manager,(file,path));assert resource and get(manager+0xbc7b0c+file*4)==resource
  current['source']=get(resource+0x108);assert bytes(m.mem_read(current['source'],len(raw)))==raw
  chunks=list(importlib.import_module('th-anm-script-dump').chunks(raw));scheduling=[]
  for index,(offset,chunk) in enumerate(chunks):
   assert chunk[32] and chunk[struct.unpack_from('<I',chunk,16)[0]]!=ord('@')
   current.update(chunk=chunk,offset=offset,index=index);before=get(resource+0x128);assert before==index+1
   assert run(0x47d230,args=(resource,))==resource
   after=get(resource+0x128);assert after==(index+2 if index+1<len(chunks) else 0);scheduling.append([before,after])
  assert get(resource+0x128)==0;current['loading']=False;put(0x4d9684,control)
  return SimpleNamespace(resource=resource,sprites=get(resource+0x11c),table=get(resource+0x120),templates=get(resource+0x10c),allocations=list(allocations),reads=list(reads),uploads=list(uploads),scheduling=scheduling)
 return SimpleNamespace(load=load,context=current,manager=manager)
