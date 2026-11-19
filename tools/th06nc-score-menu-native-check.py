"""Actual Score root states0/1 and result common ANM/time tail, 6e3a0.

Full retained owner bytes, six difficulty/Spell/Return transitions, 134-slot
ID list, keyboard chords/repeat, sounds and fade56 compared. Uses original
ANMs and actual navigation helpers. Resource/load/draw and destination-page
bodies are outside this scope; stack-cookie service is controlled.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['score-menu-update','result-state','sound-queue','anm-bank','anm-rebind','anm-vm','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-score-menu-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;fade=n.vm;digest=hashlib.sha256();offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310]
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
 def cookie(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,cookie,begin=0x1402bcf20,end=0x1402bcf20);m.mem_write(0x1404f27c8,bytes(134*384))
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,baseline)
  for p,key in [(0x9e94,'kind'),(0x9e7c,'selection'),(0x4450,'clock'),(0x4454,'pulse'),(0x9e80,'profile'),(0x9e84,'page')]:m.mem_write(n.owner+p,struct.pack('<i',c[key]))
  for i in range(3):m.mem_write(0x1404f27c8+(131+i)*384+60,struct.pack('<H',c['extra']>>i&1))
  m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['repeat']));m.mem_write(0x140509670,struct.pack('<3i',*c['beforeSounds']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140c22158,struct.pack('<Q',fade if c['beforeFade']else 0))
  if c['beforeFade']:m.mem_write(fade,bytes(c['beforeFade']))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006e3a0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=normal(m.mem_read(n.owner,0xbb48));
  if hashlib.sha256(actual).hexdigest()!=c['ownerSha256']:
   (ROOT/'tools/tmp/th06nc-score-actual.bin').write_bytes(actual);subprocess.check_output(['node','tools/th06nc-score-menu-cases.mjs','--dump='+str(index)],cwd=ROOT);wanted=(ROOT/'tools/tmp/th06nc-score-expected.bin').read_bytes();raise AssertionError((index,[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]))
  assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,c);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['afterSounds'],(index,'sounds')
  if c['afterFade']:assert bytes(m.mem_read(fade,56))==bytes(c['afterFade']),(index,'fade')
  digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-menu-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(data['cases']),stateSha256=digest.hexdigest())))
if __name__=='__main__':main()
