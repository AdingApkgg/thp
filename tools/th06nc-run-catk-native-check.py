"""Actual new-run CATK defaults3aaf6..3abcd: all134 full384-byte records.
Compares every byte and live RNG seed/count, including25728 next16 calls.
CRT memset is controlled; score loading and remaining game initialization are
separate boundaries. Production calls this before committed CATK/PSCR reload.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/gameplay-card-attack.mjs','shared/th06nc/rng.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""import{NativeRng}from'./shared/th06nc/rng.mjs';import{initializeRunCardAttackScores}from'./shared/th06nc/gameplay-card-attack.mjs';const cases=[];for(const seed of[0,1,0xbeef,65535])for(const count of[0,4294967295]){const rng=new NativeRng(seed,count),bytes=new Uint8Array(134*384).fill(165);initializeRunCardAttackScores(bytes,rng);cases.push({seed,count,rng,hex:Buffer.from(bytes).toString('hex')});}console.log(JSON.stringify(cases));"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 def memset(m,a,size,u):
  dst=m.reg_read(UC_X86_REG_RCX);value=m.reg_read(UC_X86_REG_EDX)&255;count=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([value])*count);m.reg_write(UC_X86_REG_RAX,dst);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,memset,begin=0x1402bdee2,end=0x1402bdee2)
 for c in cases:
  m.mem_write(n.assets,bytes([165])*(134*384));m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']));m.reg_write(UC_X86_REG_RSI,n.assets);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,0x6553);m.reg_write(UC_X86_REG_RBP,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003aaf6,0x14003abcd,count=1000000);actual=bytes(m.mem_read(n.assets,134*384));assert actual.hex()==c['hex'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual)
 report=dict(scope=__doc__,cases=len(cases),records=len(cases)*134,next16PerRun=25728,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-run-catk-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases),records=report['records'])))
if __name__=='__main__':main()
