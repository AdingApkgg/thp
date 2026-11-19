"""Actual 3b171..3b189 stage seed publication and RNG counter reset.

Compares snapshot, live seed and uint32 call counter; later replay/task/assets
initialization is excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/stage-rng.mjs','shared/th06nc/rng.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="import{initializeStageRng}from'./shared/th06nc/stage-rng.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[];for(const seed of [0,1,0xbeef,65535])for(const count of [0,1,12345678,4294967295]){const e={rng:new NativeRng(seed,count),replaySeed:123};initializeStageRng(e);cases.push({seed,count,e});}console.log(JSON.stringify(cases));";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for c in cases:
  m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R14,0);m.emu_start(0x14003b171,0x14003b189,count=10);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));snapshot=struct.unpack('<H',m.mem_read(n.owner+0xd408,2))[0];assert dict(rng=dict(seed=seed,count=count),replaySeed=snapshot)==c['e'];digest.update(bytes(m.mem_read(0x140a6ec40,6)))
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-stage-rng-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
