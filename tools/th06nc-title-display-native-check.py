"""Actual display submenu4dc90..4e87c, before common title tail.
All132 initialized VMs, selection/state/clocks, raw12-byte env, sounds and
ordered platform requests compared. Actual navigation/menu-item/sprite binding
execute. Render reconfiguration/display flag/file APIs controlled.
No platform display application, persistence, frame-tail or GPU claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['title-display-options','title-navigation','title-menu-item','config-file','sound-queue','anm-bank','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-title-display-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256();effects=[]
 def hook(m,a,size,u):
  if a==0x140098280:effects.append(dict(kind='setDisplayFlag',enabled=bool(m.reg_read(UC_X86_REG_ECX))))
  elif a in[0x14007c060,0x14007c320,0x14007c560]:effects.append(dict(kind='applyDisplayMode',mode={0x14007c060:2,0x14007c320:1,0x14007c560:0}[a]))
  elif a==0x1400769f0:effects.append(dict(kind='applyMusicVolume'))
  elif a==0x14007bc80:effects.append(dict(kind='restartTitleMusic'))
  elif a==0x140076780:effects.append(dict(kind='resetSound'))
  elif a==0x14007ba70:effects.append(dict(kind='saveConfig'))
  elif a==0x140039610:effects.append(dict(kind='saveEnvironmentConfig'))
  elif a==n.vm+0xf000:m.reg_write(UC_X86_REG_RAX,n.vm+0xe000)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in[0x140098280,0x14007c060,0x14007c320,0x14007c560,0x1400769f0,0x14007bc80,0x140076780,0x14007ba70,0x140039610,n.vm+0xf000]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 m.mem_write(n.vm+0xf000,b'\xc3');m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0xf000))
 baseline=bytearray(0x20000)
 for slot in data['slots']:
  b=bytearray.fromhex(slot['state'])
  for p in[0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',b,p)[0]
   if ptr:struct.pack_into('<Q',b,p,n.assetByFile[slot['file']]+ptr)
  ptr=struct.unpack_from('<Q',b,0x100)[0]
  if ptr:struct.pack_into('<Q',b,0x100,n.manager+0x608+(ptr-1)*64)
  baseline[slot['offset']:slot['offset']+288]=b
 fields=[(0x168b0,'state'),(0x28,'selection'),(0x9638,'frame'),(0x30,'pulse'),(0x1686c,'inputCooldown')]
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(baseline));effects.clear()
  for p,key in fields:m.mem_write(n.owner+p,struct.pack('<i',c['initial'][key]))
  m.mem_write(n.owner+0x16877,bytes([c['initial']['entryHold']]));m.mem_write(n.owner+0x24,struct.pack('<I',c['initial']['menuColor']));m.mem_write(n.owner+0x1a718,bytes.fromhex(c['initial']['environmentConfig']));m.mem_write(0x140a6ec50,bytes.fromhex(data['keys']));m.mem_write(0x140c21dfc,bytes.fromhex(c['environmentConfig']));m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['repeat']));m.mem_write(0x140509670,struct.pack('<3i',*c['sound']['slots']));m.mem_write(0x140509694,bytes([c['sound']['disabled']]))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf800));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14004dc90,n.stack+0xf800,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf800,(index,'stop')
  actual={key:struct.unpack('<i',m.mem_read(n.owner+p,4))[0]for p,key in fields};actual['entryHold']=bool(m.mem_read(n.owner+0x16877,1)[0])
  assert actual==c['state'],(index,'state',actual,c['state']);assert bytes(m.mem_read(0x140c21dfc,12)).hex()==c['afterEnvironment'],(index,'config');assert effects==c['effects'],(index,'effects',effects,c['effects']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,'sounds')
  vms=bytearray()
  for slot in data['slots']:
   b=bytearray(m.mem_read(n.owner+slot['offset'],288))
   for p in[0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,p)[0]
    if ptr:struct.pack_into('<Q',b,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
   ptr=struct.unpack_from('<Q',b,0x100)[0]
   if ptr:struct.pack_into('<Q',b,0x100,(ptr-n.manager-0x608)//64+1)
   vms+=b
  assert hashlib.sha256(vms).hexdigest()==c['vmSha256'],(index,'vms');digest.update(vms);digest.update(bytes.fromhex(c['afterEnvironment']))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*len(data['slots']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-display-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','vmComparisons','stateSha256']}))
if __name__=='__main__':main()

