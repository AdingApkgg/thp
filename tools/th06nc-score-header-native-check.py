"""Native 744c2..74558 score header and shared RNG side effects.

Controlled allocation bytes include nonzero padding and prior extent bytes.
Full score writer, chunk serialization, final extent/encryption and browser
lifecycle are excluded. This primitive is not yet connected to GameSave.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/score-header.mjs','shared/th06nc/rng.mjs']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{initializeScoreHeader}from'./shared/th06nc/score-header.mjs';
import{NativeRng}from'./shared/th06nc/rng.mjs';
const cases=[];for(let i=0;i<1024;i++){const seed=(i*4051)&65535,count=[0,1,0x7fffffff,0xfffffffe,0xffffffff][i%5],allocation=Uint8Array.from({length:20},(_,j)=>(i*17+j*37)&255),rng=new NativeRng(seed,count),header=initializeScoreHeader(rng,allocation);cases.push({seed,count,allocation:Buffer.from(allocation).toString('hex'),header:Buffer.from(header).toString('hex'),endSeed:rng.seed,endCount:rng.count});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))
    n=Native();m=n.m;digest=hashlib.sha256()
    for i,c in enumerate(cases):
        m.mem_write(n.assets,bytes.fromhex(c['allocation']))
        m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']))
        for reg,value in [(UC_X86_REG_RAX,n.assets),(UC_X86_REG_R15,n.owner),(UC_X86_REG_R12,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x1400744c2,0x140074558,count=1000)
        assert m.reg_read(UC_X86_REG_RIP)==0x140074558,(i,'stop')
        actual=bytes(m.mem_read(n.assets,20));rng=bytes(m.mem_read(0x140a6ec40,6))
        assert actual==bytes.fromhex(c['header']),(i,'header')
        assert rng==struct.pack('<IH',c['endCount'],c['endSeed']),(i,'RNG')
        digest.update(actual);digest.update(rng)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-header-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'cases':len(cases),'stateSha256':digest.hexdigest()}))
if __name__=='__main__':main()
