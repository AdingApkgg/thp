"""Actual Score rank pages3..7 and result common ANM/time tail, 6e3a0.

Full retained owner bytes, delayed character/mode labels, horizontal navigation,
return selection, sounds and ordered font requests compared. Actual ANM and
6dc30 helper execute; localization/name builder, font7530 metrics, Lunatic
secret producer and cookie are controlled. No draw/task/persistence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['score-rank-update','score-menu-update','result-name-scene','result-state','sound-queue','anm-bank','anm-rebind','anm-vm','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-score-rank-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;fade=n.vm;digest=hashlib.sha256();offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310]
 def normal(raw,encode=False):
  b=bytearray(raw)
  for offset in offsets:
   for p in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,offset+p)[0]
    if ptr:
     if encode:
      id=struct.unpack_from('<H',b,offset+0x38)[0]
      # Result scripts 798..7bd and background7d0..7d4 have disjoint bases.
      file='result.anm'if 0x3d70<=offset<0x4310 else next(r['file']for r in reversed(data['refs'])if r['file']!='difficulty.anm'and r['file']!='text.anm'and r['base']<=id)
      value=n.assetByFile[file]+ptr
     else:value=ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi)
     struct.pack_into('<Q',b,offset+p,value)
   ptr=struct.unpack_from('<Q',b,offset+0x100)[0]
   if ptr:struct.pack_into('<Q',b,offset+0x100,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
  return b
 baseline=bytes(normal(bytes.fromhex(data['baseline']),True))
 calls=[]
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x14006e020:calls.append(dict(kind='secret'))
  elif a==0x14006cf80:m.mem_write(m.reg_read(UC_X86_REG_RCX),f'P{m.reg_read(UC_X86_REG_EDX)} / M{m.reg_read(UC_X86_REG_R8D)}'.encode()+b'\0')
  elif a==0x140007530:
   ptr=m.reg_read(UC_X86_REG_RDX);text=bytes(m.mem_read(struct.unpack('<Q',m.mem_read(sp+0x38,8))[0],80)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];calls.append(dict(kind='font',offset=ptr-n.owner,text=text,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x14006e020,0x14006cf80,0x140007530,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,baseline)
  for p,key in [(0x9e94,'kind'),(0x9e7c,'selection'),(0x4450,'clock'),(4,'displayed')]:m.mem_write(n.owner+p,struct.pack('<i',c[key]))
  m.mem_write(n.owner+0xa8,struct.pack('<i',c['kind']-3));calls.clear()
  m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['repeat']));m.mem_write(0x140509670,struct.pack('<3i',*c['beforeSounds']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140c22158,bytes(8))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006e3a0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=normal(m.mem_read(n.owner,0xbb48));
  assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,c)
  assert calls==c['calls'],(index,'calls',calls,c['calls']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['afterSounds'],(index,'sounds')
  digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-rank-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(data['cases']),stateSha256=digest.hexdigest())))
if __name__=='__main__':main()
