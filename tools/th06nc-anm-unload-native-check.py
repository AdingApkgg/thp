"""Original ANM unload table-clearing prefix versus bank invalidation.

Stops before texture handles and allocator release. Does not verify memory/GPU
release, repeated same-slot lifetime, live process or complete resource lifecycle.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';
const bank=new AnmBank;for(const r of titleResources)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file)),r.base,{slot:r.slot});
const sprites=[...bank.sprites.keys()].sort((a,b)=>a-b),scripts=[...bank.scripts.keys()].sort((a,b)=>a-b),cases=[];
for(let slot=21;slot<=29;slot++){bank.unload(slot);cases.push({slot,active:sprites.map(id=>bank.sprites.get(id).active),scripts:scripts.map(id=>bank.scripts.has(id))});}console.log(JSON.stringify({refs:titleResources,sprites,scripts,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
    for c in data['cases']:
        for reg,value in [(UC_X86_REG_RCX,n.manager),(UC_X86_REG_RDX,c['slot']),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x140002800,0x1400028d0,count=100000)
        active=[struct.unpack('<i',m.mem_read(n.manager+0x62c+i*64,4))[0]>=0 for i in data['sprites']]
        scripts=[struct.unpack('<Q',m.mem_read(n.manager+0x23090+i*8,8))[0]!=0 for i in data['scripts']]
        assert active==c['active'];assert scripts==c['scripts'];digest.update(bytes(active+scripts))
    report=dict(scope=__doc__,unloads=len(data['cases']),spriteChecks=len(data['sprites'])*len(data['cases']),scriptChecks=len(data['scripts'])*len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/anm-bank.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-unload-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
