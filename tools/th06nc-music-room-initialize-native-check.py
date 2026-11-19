"""Music Room initial owner 58cc0..591d9, actual background/header ANMs.

Full 0x3d18-byte owner, fade56 and ordered title/font/description/achievement
requests compared. Resource calls use already loaded original ANMs; actual
musiccmt parser runs. UCRT scanner, localization lookup, font7530 metrics,
description publisher, allocation/free and platform achievement services are
controlled. Task registration, description tail, raster/audio excluded here.
"""
import hashlib,json,re,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['music-room-initialize','music-room-state','music-room-table','music-unlock','anm-rebind','anm-bank','anm-vm','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-music-room-initialize-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;program=n.assets+0x100000;records=n.assets+0x110000;text=n.assets+0x120000;fade=n.vm;raw=bytes.fromhex(data['table']);m.mem_write(program,raw+b'\0');calls=[];localization={};digest=hashlib.sha256()
 offsets=[8+i*288 for i in range(32)]+[0x2448+i*288 for i in range(6)]
 def cstring(ptr):
  raw=bytearray()
  while(b:=m.mem_read(ptr+len(raw),1)[0]):raw.append(b)
  return raw.decode('utf-8')
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x140058f08:
   key=cstring(m.reg_read(UC_X86_REG_RBX));m.mem_write(text,localization.get(key,key).encode()+b'\0');m.reg_write(UC_X86_REG_RBX,text);m.reg_write(UC_X86_REG_RSI,0);m.reg_write(UC_X86_REG_RIP,0x140058ff2);return
  if a==0x1400590a5:calls.extend([dict(kind='achievement',key='Achievement22'),dict(kind='commit')]);m.reg_write(UC_X86_REG_RIP,0x1400590d8);return
  if a==0x1400020b0:m.reg_write(UC_X86_REG_RAX,0)
  elif a==0x1400387a0:m.mem_write(m.reg_read(UC_X86_REG_R8),struct.pack('<I',len(raw)));m.reg_write(UC_X86_REG_RAX,program)
  elif a==0x1402bd4a0:assert m.reg_read(UC_X86_REG_RCX)==0x1080;m.reg_write(UC_X86_REG_RAX,records)
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  elif a==0x14003a180:
   found=re.match(r'^data/bgm/th06_([0-9]+)',cstring(m.reg_read(UC_X86_REG_RCX)));assert found;m.mem_write(m.reg_read(UC_X86_REG_R8),struct.pack('<i',int(found[1])));m.reg_write(UC_X86_REG_EAX,1)
  elif a==0x140007530:
   ptr=m.reg_read(UC_X86_REG_RDX);value=cstring(struct.unpack('<Q',m.mem_read(sp+0x38,8))[0]);colors=[m.reg_read(UC_X86_REG_R8)&0xffffffff,m.reg_read(UC_X86_REG_R9)&0xffffffff,*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];i=(ptr-n.owner-8)//288;key=f'MD_{i:02d}_TITLE'if(1<<i)&unlockedMask else'MD_LOCKED_TITLE';calls.append(dict(kind='font',offset=ptr-n.owner,key=key,text=value,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
  elif a==0x1400591e0:calls.append(dict(kind='description',key=cstring(m.reg_read(UC_X86_REG_RDX)),initial=bool(m.reg_read(UC_X86_REG_R8)&255)))
  elif a not in [0x1402bcf20,0x1402b0380]:raise AssertionError(hex(a))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 # free uses the executable IAT target; map it to the same observed no-op.
 freePointer=struct.unpack('<Q',m.mem_read(0x1402c0378,8))[0]
 addresses=[0x140058f08,0x1400590a5,0x1400020b0,0x1400387a0,0x1402bd4a0,0x1402bdee2,0x14003a180,0x140007530,0x1400591e0,0x1402bcf20]
 # 5915d calls the free-import slot directly; redirect that import to a mapped stub.
 freeStub=n.assets+0x1f0000;m.mem_write(freeStub,b'\xc3');m.mem_write(0x1402c0378,struct.pack('<Q',freeStub))
 for a in addresses:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for index,c in enumerate(data['cases']):
  localization=c['localization'];unlockedMask=c['unlockedMask'];m.mem_write(n.owner,bytes(0x3d18));m.mem_write(fade,bytes(c['beforeFade']));m.mem_write(0x140c22158,struct.pack('<Q',fade));m.mem_write(0x1404ff160,struct.pack('<I',unlockedMask));calls.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140058cc0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=bytearray(m.mem_read(n.owner,0x3d18));struct.pack_into('<Q',actual,0x2438,0x1000)
  for offset in offsets:
   for p in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',actual,offset+p)[0]
    if ptr:
     base=next(lo for lo,hi in n.ranges if lo<=ptr<hi);struct.pack_into('<Q',actual,offset+p,ptr-base)
   ptr=struct.unpack_from('<Q',actual,offset+0x100)[0]
   if ptr:struct.pack_into('<Q',actual,offset+0x100,(ptr-n.manager-0x608)//64+1)
  wanted=bytes.fromhex(c['owner']);assert actual==wanted,(index,[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:16]);assert bytes(m.mem_read(fade,56))==bytes(c['afterFade']),(index,'fade');assert calls==c['calls'],(index,'requests',calls,c['calls']);assert m.reg_read(UC_X86_REG_EAX)==0;digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),requests=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-music-room-initialize-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['passed','cases','requests','stateSha256']}))

if __name__=='__main__':main()
