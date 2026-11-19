"""Spell character/profile refresh 4f150 and 4f1f0, full affected ANM VMs.

Actual loaded resources and native setters; resource transport, text/info refresh,
draw/GPU and overall menu integration are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['spell-practice-profile','spell-practice-layout','title-selection-layout','anm-initialize','anm-rebind']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{selectionResources}from'./shared/th06nc/title-selection-layout.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{spellMenuAsset,initializeSpellMenuAnimations}from'./shared/th06nc/spell-practice-layout.mjs';import{refreshSpellCharacter,refreshSpellProfile}from'./shared/th06nc/spell-practice-profile.mjs';
const refs=[...selectionResources,spellMenuAsset],resources=new Map([...titleResources,...refs].map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])),cases=[];
const snap=g=>[...g.slots].filter(([offset])=>offset>=0x122e0&&offset<0x13ba0||offset>=0x19998).map(([offset,vm])=>({offset,file:[...resources].find(([file,r])=>r===vm.resource)?.[0],state:Buffer.from(vm.state).toString('hex')}));
for(const profile of [0,1,2,3])for(const direction of [-1,0,1])for(const ticks of [0,15,40]){
 const g=new TitleAnimations(resources);initializeSpellMenuAnimations(g,resources);const state={stageDirection:99,stageTransition:17,orderDirection:99,orderTransition:17,difficultyTransition:18,profileTransition:19};
 refreshSpellCharacter(g,state,1,1);refreshSpellProfile(g,state,1,1,1);for(let n=0;n<ticks;n++)for(const vm of g.slots.values())if(vm.pointer(0xf8))vm.tick();
 const before=snap(g),initial={...state};refreshSpellCharacter(g,state,profile>>1,direction);refreshSpellProfile(g,state,profile>>1,profile&1,direction);cases.push({profile,direction,ticks,before,initial,state,after:snap(g)});
}console.log(JSON.stringify({refs,cases}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;fields={'stageDirection':0x168f0,'stageTransition':0x168ec,'orderDirection':0x168f8,'orderTransition':0x168f4,'difficultyTransition':0x168fc,'profileTransition':0x16900};digest=hashlib.sha256()
 def normalized(raw,to_native,file=None):
  raw=bytearray(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,n.assetByFile[file]+ptr if to_native else ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,n.manager+0x608+(ptr-1)*64 if to_native else(ptr-n.manager-0x608)//64+1)
  return bytes(raw)
 for i,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(0x20000))
  for slot in c['before']:m.mem_write(n.owner+slot['offset'],normalized(bytes.fromhex(slot['state']),True,slot.get('file')))
  for key,offset in fields.items():m.mem_write(n.owner+offset,struct.pack('<i',c['initial'][key]))
  m.mem_write(0x1404f1e80,bytes([c['profile']>>1,c['profile']&1]))
  for address in [0x14004f150,0x14004f1f0]:
   sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,c['direction']&0xffffffffffffffff);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  for key,offset in fields.items():assert struct.unpack('<i',m.mem_read(n.owner+offset,4))[0]==c['state'][key],(i,key)
  for slot in c['after']:
   actual=normalized(m.mem_read(n.owner+slot['offset'],288),False);expected=bytes.fromhex(slot['state']);diff=[hex(j)for j,(a,b)in enumerate(zip(actual,expected))if a!=b];assert not diff,(i,hex(slot['offset']),diff);digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),vmsPerCase=len(data['cases'][0]['after']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-profile-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':report['cases'],'vmsPerCase':report['vmsPerCase'],'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
