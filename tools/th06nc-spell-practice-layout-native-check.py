"""Spell-title ANM setup 4c781..4ca1a with actual selection/spell resources.

Compares all 33 initialized 288-byte VMs. Text/font initialization, resource
transport/unload, later profile/info helpers, common tick and GPU are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['spell-practice-layout','title-selection-layout','title-animations','anm-bank','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{selectionResources}from'./shared/th06nc/title-selection-layout.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{spellMenuAsset,initializeSpellMenuAnimations}from'./shared/th06nc/spell-practice-layout.mjs';
const refs=[...selectionResources,spellMenuAsset],resources=new Map([...titleResources,...refs].map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])),g=new TitleAnimations(resources);initializeSpellMenuAnimations(g,resources);console.log(JSON.stringify({refs,slots:[...g.slots].filter(([offset])=>offset>=0x122e0&&offset<0x13ba0||offset>=0x19998).map(([offset,vm])=>({offset,state:Buffer.from(vm.state).toString('hex')}))}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m
 m.mem_write(n.owner+0x168d3,b'\1')
 for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,8),(UC_X86_REG_R14,0x17d)]:m.reg_write(reg,value)
 m.emu_start(0x14004c781,0x14004ca1a,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x14004ca1a
 digest=hashlib.sha256()
 for slot in data['slots']:
  actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',actual,p)[0]
   if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',actual,0x100)[0]
  if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
  wanted=bytes.fromhex(slot['state']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(hex(slot['offset']),diff);digest.update(actual)
 assert len(data['slots'])==33
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,vms=len(data['slots']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'vms':report['vms'],'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
