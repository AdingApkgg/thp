"""Credits initialization tail14ac1..14c8c and entire update13790.
Full31c8 owner, fade56, sounds, return status/global and ordered font calls.
Actual native sprite resets/binding and counters run. JSON/vector resource
admission supplied; fonts use controlled metrics. No draw/task/GPU claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['credits-state','credits-update','anm-rebind','anm-bank','anm-vm','fade','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-credits-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;calls=[];digest=hashlib.sha256();fade=n.vm
 def font(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x140007530:
   ptr=m.reg_read(UC_X86_REG_RDX);s=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];text=bytes(m.mem_read(s,400)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];calls.append(dict(kind='font',offset=ptr-n.owner,text=text,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in[0x140007530,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,font,begin=a,end=a)
 def pages(variant):
  first=n.assets+0x100000;rows=n.assets+0x110000;strings=n.assets+0x150000;desc=n.assets+0x1f0000
  for i,page in enumerate(data['variants'][variant]):
   start=rows
   for value in page:
    raw=value.encode();b=bytearray(32)
    if len(raw)<16:b[:len(raw)]=raw;struct.pack_into('<2Q',b,16,len(raw),15)
    else:m.mem_write(strings,raw+b'\0');struct.pack_into('<Q',b,0,strings);struct.pack_into('<2Q',b,16,len(raw),len(raw));strings+=len(raw)+1
    m.mem_write(rows,bytes(b));rows+=32
   m.mem_write(first+i*24,struct.pack('<3Q',start,rows,rows))
  m.mem_write(desc,struct.pack('<3Q',first,first+len(data['variants'][variant])*24,first+len(data['variants'][variant])*24));m.mem_write(n.owner+0x40,struct.pack('<Q',desc))
 def normalized(raw,encode=False):
  b=bytearray(raw);b[0x40:0x48]=bytes(8)
  for i in range(44):
   p=0x48+i*288+0x100;ptr=struct.unpack_from('<Q',b,p)[0]
   if ptr:struct.pack_into('<Q',b,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
  return b
 for index,c in enumerate(data['initializations']):
  m.mem_write(n.owner,bytes(0x31c8));pages(c['variant']);m.mem_write(n.owner+0x30,struct.pack('<i',len(data['variants'][c['variant']])));m.mem_write(fade,bytes(56));m.mem_write(fade+0x34,struct.pack('<i',c['mode']));m.mem_write(0x140c22158,struct.pack('<Q',fade));calls.clear()
  for reg,value in[(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBP,n.stack+0x8100)]:m.reg_write(reg,value)
  m.mem_write(n.stack+0x8070,struct.pack('<Q',n.owner))
  m.emu_start(0x140014ac1,0x140014c8c,count=100000);actual=normalized(m.mem_read(n.owner,0x31c8));assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,'initial owner');assert calls==c['calls'],(index,'initial calls');assert bytes(m.mem_read(fade,56)).hex()==c['fade'],(index,'initial fade');digest.update(actual)
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(normalized(bytes.fromhex(c['before']),True)));pages(c['variant']);m.mem_write(fade,bytes(56));m.mem_write(0x140c22158,struct.pack('<Q',fade));m.mem_write(0x140509670,struct.pack('<3i',*c['beforeSounds']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x140c21d9c,bytes(4));calls.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140013790,n.stack+0xf000,count=100000);result=m.reg_read(UC_X86_REG_EAX);assert result==c['result'],(index,'result');
  if result==0:calls.append(dict(kind='title'));assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==1
  actual=normalized(m.mem_read(n.owner,0x31c8));assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,'owner');assert calls==c['calls'],(index,'calls',calls,c['calls']);assert bytes(m.mem_read(fade,56)).hex()==c['fade'],(index,'fade');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,'sounds');digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,initializations=len(data['initializations']),cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,originalCreditSha256=data['rawSha256'],executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-credits-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','initializations','cases','stateSha256']}))
if __name__=='__main__':main()
