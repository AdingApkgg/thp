"""Music Room description publication tail 59490..59598.

Original sixteen-row reset/binding, nonempty/empty visibility, positions and
font requests. Full retained owner bytes compared. Localization and getline
vector construction are supplied inputs; font7530 uses controlled metrics.
No raster/glyph/GPU or full initial loader/task equivalence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['music-room-description','music-room-state','anm-rebind','anm-bank','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-music-description-cases.mjs'],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;calls=[];digest=hashlib.sha256()
 def normal(raw,encode=False):
  b=bytearray(raw)
  for i in range(16):
   offset=0x2b10+i*288
   for p in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,offset+p)[0]
    if ptr:struct.pack_into('<Q',b,offset+p,n.assets+ptr if encode else ptr-n.assets)
   ptr=struct.unpack_from('<Q',b,offset+0x100)[0]
   if ptr:struct.pack_into('<Q',b,offset+0x100,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
  return b
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);ptr=m.reg_read(UC_X86_REG_RDX);textptr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];raw=bytearray()
  while(b:=m.mem_read(textptr+len(raw),1)[0]):raw.append(b)
  colors=[m.reg_read(UC_X86_REG_R8)&0xffffffff,m.reg_read(UC_X86_REG_R9)&0xffffffff,*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))]
  calls.append(dict(offset=ptr-n.owner,text=raw.decode('utf-8'),colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140007530,end=0x140007530)
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(normal(bytes.fromhex(c['before']),True)));vector=n.assets+0x100000;strings=vector+0x10000
  for i,line in enumerate(c['lines']):
   raw=line.encode();block=bytearray(32)
   if len(raw)<=15:block[:len(raw)]=raw;capacity=15
   else:struct.pack_into('<Q',block,0,strings+i*0x1000);m.mem_write(strings+i*0x1000,raw+b'\0');capacity=len(raw)
   struct.pack_into('<QQ',block,16,len(raw),capacity);m.mem_write(vector+i*32,bytes(block))
  sp=n.stack+0x7000;m.mem_write(sp+0x58,struct.pack('<QQ',vector,vector+len(c['lines'])*32));calls.clear()
  for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,sp+0x100),(UC_X86_REG_R15,n.owner),(UC_X86_REG_R12,int(c['initial'])),(UC_X86_REG_R13,0)]:m.reg_write(reg,value)
  m.emu_start(0x140059490,0x140059598,count=100000);assert m.reg_read(UC_X86_REG_RIP)==0x140059598
  actual=normal(m.mem_read(n.owner,0x3d18));wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,c['key'],[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:12]);assert calls==c['calls'],(index,'calls',calls,c['calls']);digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),fontRequests=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-music-description-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['passed','cases','fontRequests','stateSha256']}))

if __name__=='__main__':main()
