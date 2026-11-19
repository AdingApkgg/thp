"""Actual387a0 localized-then-base16-archive lookup, including bypass decision.
C++ string construction/insertion/growth, CRT byte copy and archive extraction
are controlled services. Actual basename/suffix composition and name comparison
order execute. GPU, filesystem reads and archive decoding excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/localized-asset.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();cases=json.loads(subprocess.check_output(['node','tools/th06nc-localized-asset-cases.mjs'],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x100000);cursor=heap;active={};archiveTokens={};digest=hashlib.sha256()
 def u64(p):return struct.unpack('<Q',m.mem_read(p,8))[0]
 def raw(p):
  b=bytearray()
  while True:
   c=bytes(m.mem_read(p+len(b),1))[0]
   if not c:return bytes(b)
   b.append(c)
 def get(p):
  length,capacity=struct.unpack('<QQ',m.mem_read(p+16,16));return bytes(m.mem_read(p if capacity<=15 else struct.unpack('<Q',m.mem_read(p,8))[0],length))
 def put(p,b):
  nonlocal cursor
  if len(b)<=15:m.mem_write(p,b.ljust(16,b'\0')+struct.pack('<QQ',len(b),15))
  else:
   ptr=cursor;cursor+=((len(b)+64+15)//16)*16;m.mem_write(ptr,b+b'\0');m.mem_write(p,struct.pack('<QQQQ',ptr,0,len(b),len(b)+63))
 def finish(value=0):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,value)
 def hook(m,a,size,u):
  rcx=m.reg_read(UC_X86_REG_RCX);rdx=m.reg_read(UC_X86_REG_RDX);r8=m.reg_read(UC_X86_REG_R8);r9=m.reg_read(UC_X86_REG_R9)
  if a==0x140038a41:active.setdefault('names',[]).append(raw(r8));return
  if a==0x140038a10:active['candidate']=raw(m.reg_read(UC_X86_REG_R11));active['root']=hex(m.reg_read(UC_X86_REG_R13));active['slot0']=hex(u64(m.reg_read(UC_X86_REG_R13)));return
  if a==0x140038b58:active['bypassPath']=raw(rcx);m.emu_stop();return
  if a==0x140008350:put(rcx,bytes(m.mem_read(rdx,r8)));finish(rcx)
  elif a==0x140008650:
   b=get(rcx);put(rcx,b[:rdx]+bytes(m.mem_read(r8,r9))+b[rdx:]);finish(rcx)
  elif a==0x140008410:finish(rcx)
  elif a==0x1400082d0:
   b=bytes(m.mem_read(rcx,rdx));pos=b.rfind(b'.');finish(pos&0xffffffffffffffff)
  elif a==0x140018e00:
   sp=m.reg_read(UC_X86_REG_RSP);length=struct.unpack('<Q',m.mem_read(sp+0x28,8))[0];put(rcx,get(rcx)+bytes(m.mem_read(r9,length)));finish(rcx)
  elif a in [0x1402bdee8,0x1402bdeee]:m.mem_write(rcx,bytes(m.mem_read(rdx,r8)));finish(rcx)
  elif a==n.vm+0x9000:
   b=raw(rcx);pos=b.rfind(bytes([rdx&255]));finish(rcx+pos if pos>=0 else 0)
  elif a==0x14005a470:finish(archiveTokens[(rcx,rdx)])
  elif a==0x1402bcf20:finish(m.reg_read(UC_X86_REG_RAX))
 addresses=[0x140038a41,0x140038a10,0x140038b58,0x140008350,0x140008650,0x140008410,0x1400082d0,0x140018e00,0x1402bdee8,0x1402bdeee,n.vm+0x9000,0x14005a470,0x1402bcf20]
 for a in addresses:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 m.mem_write(0x1402c02e8,struct.pack('<Q',n.vm+0x9000))
 for index,c in enumerate(cases):
  cursor=heap;active.clear();archiveTokens.clear();m.mem_write(0x140c21980,bytes(128));m.mem_write(n.stack,bytes(0x10000));put(0x1404ff380,c['language'].encode());m.mem_write(n.owner,c['path'].encode()+b'\0')
  for slot,archive in enumerate(c['archives'][:16]):
   if archive is None:continue
   ptr=n.assets+slot*0x1000;entries=ptr+0x100;m.mem_write(ptr,struct.pack('<QIIQ',0,len(archive['entries']),0,entries));m.mem_write(0x140c21980+slot*8,struct.pack('<Q',ptr))
   for entryIndex,entry in enumerate(archive['entries']):m.mem_write(entries+entryIndex*288,bytes(288));m.mem_write(entries+entryIndex*288+32,entry['name'].encode()+b'\0');archiveTokens[(ptr,entryIndex)]=0x10000+slot*256+entryIndex
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,int(c['bypass']));m.reg_write(UC_X86_REG_R8,0);m.emu_start(0x1400387a0,n.stack+0xf000,count=100000)
  e=c['expected']
  if c['bypass']:assert active.get('bypassPath')==c['path'].encode(),(index,c)
  else:
   expected=0 if e is None else 0x10000+e['archiveIndex']*256+e['entryIndex'];actual=m.reg_read(UC_X86_REG_RAX);assert actual==expected,(index,c,hex(actual),hex(m.reg_read(UC_X86_REG_RIP)),active);digest.update(struct.pack('<Q',actual))
 assert sha==hashlib.sha256((ROOT/source).read_bytes()).hexdigest();report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-localized-asset-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
