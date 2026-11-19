"""First base selection ANM initialization after table loading, original x64.

Excludes texture loading, Spell-specific setup, owner tail/state clocks, GPU
and gameplay. Current check starts selection slots at their initial zero state.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_R14,UC_X86_REG_RDI,UC_X86_REG_RBX


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{selectionResources,initializeSelectionAnimations}from'./shared/th06nc/title-selection-layout.mjs';
const resources=new Map([...titleResources,...selectionResources].map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])),g=new TitleAnimations(resources);initializeSelectionAnimations(g,resources);console.log(JSON.stringify({refs:selectionResources,slots:[...g.slots].filter(([offset])=>offset>=0x122e0&&offset<0x13ba0).map(([offset,v])=>({offset,state:Buffer.from(v.state).toString('hex')}))}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m
    for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R14,0x17d),(UC_X86_REG_RDI,n.owner+0x1595d),(UC_X86_REG_RBX,n.owner+0x122e0)]:m.reg_write(reg,value)
    m.emu_start(0x14004af40,0x14004afb9,count=1000000)
    assert len(data['slots'])==22;digest=hashlib.sha256()
    for slot in data['slots']:
        actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
        ptr=struct.unpack_from('<Q',actual,0x100)[0]
        if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(slot['state']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,wanted)) if x!=y];assert not diff,(slot['offset'],diff);digest.update(actual)
    report=dict(scope=__doc__,slots=len(data['slots']),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-selection-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-selection-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
