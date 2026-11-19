"""Actual controller key submenu49acc..4aa92 before common title tail.
All132 initialized VMs, state/clocks, five binding selections, rawcfg/runtime
keys, previous button, sounds and requests compared. Actual navigation,
original Xbox icon binding and duplicate-swap helper execute. Device kind0
and18-byte button input supplied; input API/texture loading controlled.
No physical controller/application/persistence/frame-tail/draw/GPU claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['title-key-options','title-navigation','title-menu-item','config-file','sound-queue','anm-bank','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-title-keys-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256();effects=[]
 def hook(m,a,size,u):
  if a in[0x14004cbf4,0x140047f60]:m.emu_stop();return
  if a==0x140067bc0:m.reg_write(UC_X86_REG_RAX,0)
  elif a==0x140012b40:m.reg_write(UC_X86_REG_RAX,n.vm+0xd000)
  elif a==0x1400769f0:effects.append(dict(kind='applyMusicVolume'))
  elif a==0x14007bc80:effects.append(dict(kind='restartTitleMusic'))
  elif a==0x140076780:effects.append(dict(kind='resetSound'))
  elif a==0x14007ba70:effects.append(dict(kind='saveConfig'))
  elif a==0x140039610:effects.append(dict(kind='saveEnvironmentConfig'))
  elif a==n.vm+0xf000:m.reg_write(UC_X86_REG_RAX,n.vm+0xe000)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in[0x14004cbf4,0x140047f60,0x140067bc0,0x140012b40,0x1400769f0,0x14007bc80,0x140076780,0x14007ba70,0x140039610,n.vm+0xf000]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
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
  m.mem_write(n.owner+0x24,struct.pack('<I',c['initial']['menuColor']));m.mem_write(n.owner+0x168c0,struct.pack('<5h',*c['initial']['keySelections']));m.mem_write(0x140a6ec30,struct.pack('<h',c['beforeButton']));m.mem_write(n.vm+0xd000,bytes.fromhex(c['buttons']));m.mem_write(0x140c21f68,bytes(4));m.mem_write(n.owner+0x16877,bytes([c['initial']['entryHold']]));m.mem_write(0x140c21da4,bytes.fromhex(c['config']));m.mem_write(0x140a6ec50,bytes.fromhex(data['keys']));m.mem_write(0x140c21dfc,bytes.fromhex(data['environmentConfig']));m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['repeat']));m.mem_write(0x140509670,struct.pack('<3i',*c['sound']['slots']));m.mem_write(0x140509694,bytes([c['sound']['disabled']]))
  for reg,value in[(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R12,28),(UC_X86_REG_R13,11),(UC_X86_REG_R15,256),(UC_X86_REG_RDI,8),(UC_X86_REG_R14,24)]:m.reg_write(reg,value)
  m.mem_write(n.stack+0x8030,struct.pack('<i',6));m.emu_start(0x140049acc,n.stack,count=1000000);assert m.reg_read(UC_X86_REG_RIP)in[0x14004cbf4,0x140047f60],(index,'stop')
  actual={key:struct.unpack('<i',m.mem_read(n.owner+p,4))[0]for p,key in fields};actual['entryHold']=bool(m.mem_read(n.owner+0x16877,1)[0])
  actual['keySelections']=list(struct.unpack('<5h',m.mem_read(n.owner+0x168c0,10)))
  assert actual==c['state'],(index,'state',actual,c['state']);assert bytes(m.mem_read(0x140c21da4,44)).hex()==c['afterConfig'],(index,'config');assert effects==c['effects'],(index,'effects',effects,c['effects']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,'sounds')
  assert bytes(m.mem_read(0x140a6ec50,10)).hex()==c['afterKeys'],(index,'keys');assert struct.unpack('<h',m.mem_read(0x140a6ec30,2))[0]==c['afterButton'],(index,'button')
  vms=bytearray()
  for slot in data['slots']:
   b=bytearray(m.mem_read(n.owner+slot['offset'],288))
   for p in[0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,p)[0]
    if ptr:struct.pack_into('<Q',b,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
   ptr=struct.unpack_from('<Q',b,0x100)[0]
   if ptr:struct.pack_into('<Q',b,0x100,(ptr-n.manager-0x608)//64+1)
   vms+=b
  assert hashlib.sha256(vms).hexdigest()==c['vmSha256'],(index,'vms');digest.update(vms);digest.update(bytes.fromhex(c['afterConfig']))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*len(data['slots']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-keys-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','vmComparisons','stateSha256']}))
if __name__=='__main__':main()

