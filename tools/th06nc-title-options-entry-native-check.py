"""Actual title Options entry/return-delay prefix4cbf4..4cd1a.
132 initialized VM interrupt fields and owner flags/delay compared. Original
item-to-group helper46550 executes; no input/body/common ANM tail/draw claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/title-options-entry.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-title-options-entry-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
 def stop(m,a,size,u):m.emu_stop()
 m.hook_add(UC_HOOK_CODE,stop,begin=0x14004cd1a,end=0x14004cd1a)
 baseline=bytearray(0x20000)
 for slot in data['slots']:
  b=bytearray.fromhex(slot['state'])
  for p in[0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',b,p)[0]
   if ptr:struct.pack_into('<Q',b,p,n.assetByFile[slot['file']]+ptr)
  ptr=struct.unpack_from('<Q',b,0x100)[0]
  if ptr:struct.pack_into('<Q',b,0x100,n.manager+0x608+(ptr-1)*64)
  baseline[slot['offset']:slot['offset']+288]=b
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(baseline));m.mem_write(n.owner+0x168b0,struct.pack('<i',c['initial']['state']));m.mem_write(n.owner+0x9638,struct.pack('<i',c['initial']['frame']));m.mem_write(n.owner+0x16878,bytes([c['initial']['optionsEntry']]));m.mem_write(n.owner+0x1687c,struct.pack('<i',c['initial']['inputDelay']))
  for reg,value in[(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R13,c['previousState']),(UC_X86_REG_R15,3)]:m.reg_write(reg,value)
  m.mem_write(n.stack+0x8030,struct.pack('<i',c['previousState']));m.emu_start(0x14004cbf4,n.stack,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x14004cd1a
  assert bool(m.mem_read(n.owner+0x16878,1)[0])==c['result']['optionsEntry'],(index,'entry');assert struct.unpack('<i',m.mem_read(n.owner+0x1687c,4))[0]==c['result']['inputDelay'],(index,'delay')
  vms=bytearray()
  for slot in data['slots']:
   b=bytearray(m.mem_read(n.owner+slot['offset'],288))
   for p in[0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,p)[0]
    if ptr:struct.pack_into('<Q',b,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
   ptr=struct.unpack_from('<Q',b,0x100)[0]
   if ptr:struct.pack_into('<Q',b,0x100,(ptr-n.manager-0x608)//64+1)
   vms+=b
  assert hashlib.sha256(vms).hexdigest()==c['vmSha256'],(index,'vms');digest.update(vms)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*len(data['slots']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-options-entry-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','vmComparisons','stateSha256']}))
if __name__=='__main__':main()

