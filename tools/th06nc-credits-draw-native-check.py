"""Actual Credits draw13bf0, complete31c8 owner/ASCII queue/requests.
Original UCRT measures and formats page labels.44 VM slide/alpha requests,
footer old/new crossfade and queue capacity compared; background API observed.
GPU/background raster/font raster/task lifetime excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['credits-draw','credits-state','credits-update','ascii-text','score-popup-draw','anm-bank','anm-vm','anm-rebind']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-credits-draw-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;font=0x1403de620;shim=n.vm+0x9000;m.mem_write(shim,b'\xc3');m.mem_write(0x1402c0528,struct.pack('<Q',shim));crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p];calls=[];digest=hashlib.sha256();offsets=[0x48+i*288 for i in range(44)]
 def normal_vm(raw):
  b=bytearray(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',b,p)[0]
   if ptr:struct.pack_into('<Q',b,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',b,0x100)[0]
  if ptr:struct.pack_into('<Q',b,0x100,(ptr-n.manager-0x608)//64+1)
  return b
 baseline=bytearray.fromhex(data['baseline'])
 for offset in offsets:
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',baseline,offset+p)[0]
   if ptr:
    file='text.anm';struct.pack_into('<Q',baseline,offset+p,n.assetByFile[file]+ptr)
  ptr=struct.unpack_from('<Q',baseline,offset+0x100)[0]
  if ptr:struct.pack_into('<Q',baseline,offset+0x100,n.manager+0x608+(ptr-1)*64)
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x1400078a0:calls.append(dict(kind='background',color=struct.unpack('<I',m.mem_read(n.manager+0x20f80,4))[0]))
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  elif a in [0x140002a80,0x1400036c0]:
   ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(snap=True,offset=ptr-n.owner,path='flat'if a==0x140002a80 else'rotated',state=normal_vm(m.mem_read(ptr,288)).hex()))
  elif a==shim:
   fmt=bytes(m.mem_read(m.reg_read(UC_X86_REG_R9),100)).split(b'\0')[0];va=struct.unpack('<Q',m.mem_read(sp+0x30,8))[0];values=list(struct.unpack('<8Q',m.mem_read(va,64)));buffers=[]
   if b'%*s'in fmt:
    raw=bytes(m.mem_read(values[3],100)).split(b'\0')[0];buffers.append(ctypes.create_string_buffer(raw));values[3]=ctypes.addressof(buffers[-1])
   args=(ctypes.c_uint64*8)(*values);target=m.reg_read(UC_X86_REG_RDX);out=ctypes.create_string_buffer(512);length=formatter(m.reg_read(UC_X86_REG_RCX),out if target else None,m.reg_read(UC_X86_REG_R8),fmt,None,args);assert length>=0,(fmt,length);m.reg_write(UC_X86_REG_RAX,length)
   if target:m.mem_write(target,out.value+b'\0')
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1400078a0,0x140002a80,0x1400036c0,shim,0x1402bdee2,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(address,rcx):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(baseline))
  for p,key in[(0x1c,'reveal'),(0x20,'slide'),(0x24,'direction'),(0x38,'exitClock'),(0x30,'total'),(0x18,'pulse')]:m.mem_write(n.owner+p,struct.pack('<i',c[key]))
  m.mem_write(n.owner+0x2c,struct.pack('<i',((c['total']-1)//2)*2));m.mem_write(n.owner+0x28,bytes(4))
  for row in range(44):m.mem_write(n.owner+0x48+row*288+0xec,struct.pack('<I',0x7f123456 if row%2 else 0xffabcdef))
  m.mem_write(font,bytes(0xdbb8));run(0x140009790,font);m.mem_write(font+0x7bb0,struct.pack('<i',c['cursor']));m.mem_write(font,struct.pack('<f',c['scale']));calls.clear();run(0x140013bf0,n.owner)
  owner=bytearray(m.mem_read(n.owner,0x31c8))
  for offset in offsets:owner[offset:offset+288]=normal_vm(owner[offset:offset+288])
  assert hashlib.sha256(owner).hexdigest()==c['ownerSha256'],(index,'owner',c)
  assert calls==c['calls'],(index,'draws',len(calls),len(c['calls']),next((i for i,(a,b)in enumerate(zip(calls,c['calls']))if a!=b),None))
  ascii=bytearray(m.mem_read(font,0xdbb8))
  for offset in [0x10,0x130]:ascii[offset:offset+288]=normal_vm(ascii[offset:offset+288])
  assert hashlib.sha256(ascii).hexdigest()==c['asciiSha256'],(index,'ascii',c['reveal'],c['pulse'],c['cursor']);digest.update(owner);digest.update(ascii)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),drawRequests=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-credits-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['passed','cases','drawRequests','stateSha256']}))

if __name__=='__main__':main()
