"""Compare title ANM group initialization with original loaders and VM setters.

Headless, nine base Japanese title ANMs. Not the complete title owner startup,
disabled-state computation, localization, input, audio, drawing or game acceptance.
"""
import hashlib,importlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RBX,UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_R14,UC_X86_REG_R15,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RCX,UC_X86_REG_RDX
ROOT=Path(__file__).resolve().parents[1]


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';
const refs=titleResources.map(r=>({...r,path:'runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file}));
const a=new TitleAnimations(new Map(refs.map(r=>[r.file,readAnm(readFileSync(r.path))])));
console.log(JSON.stringify({refs,slots:[...a.slots].map(([offset,v])=>({offset,id:v.v.getUint16(0x38,true),state:Buffer.from(v.state).toString('hex')}))}));
"""
    expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());b=Path(target['executable']).read_bytes();assert hashlib.sha256(b).hexdigest()==target['sha256']
    m=Uc(UC_ARCH_X86,UC_MODE_64);m.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(b):m.mem_write(0x140000000+s['va'],b[s['raw']:s['raw']+s['rawsize']])
    assets,manager,stack,vm=0x70000000,0x71000000,0x72000000,0x73000000
    for addr,size in [(assets,0x100000),(manager,0x40000),(stack,0x10000),(vm,0x10000)]:m.mem_map(addr,size)
    ranges=[]
    for index,ref in enumerate(expected['refs']):
        asset=assets+index*0x10000;raw=bytearray((ROOT/ref['path']).read_bytes());assert len(raw)<0x10000
        struct.pack_into('<I',raw,8,ref['slot']);m.mem_write(asset,bytes(raw));ranges.append((asset,asset+len(raw)))
        m.mem_write(manager+8+ref['slot']*8,struct.pack('<Q',asset))
        for reg,val in [(UC_X86_REG_RBX,manager),(UC_X86_REG_RDI,asset),(UC_X86_REG_RSI,ref['slot']),(UC_X86_REG_R14,0),(UC_X86_REG_R15,ref['base']),(UC_X86_REG_RBP,stack+0x8100),(UC_X86_REG_RSP,stack+0x8000)]:m.reg_write(reg,val)
        m.emu_start(0x1400024ae,0x14000270b,count=1000000)
    m.mem_write(0x140a6e9b0,struct.pack('<Q',manager));digest=hashlib.sha256()
    for slot in expected['slots']:
        m.mem_write(vm,bytes(0x120));sp=stack+0x8008;m.mem_write(sp,struct.pack('<Q',stack))
        for reg,val in [(UC_X86_REG_RCX,vm),(UC_X86_REG_RDX,slot['id']),(UC_X86_REG_RSP,sp)]:m.reg_write(reg,val)
        m.emu_start(0x140046dc0,stack,count=1000000)
        assert m.reg_read(UC_X86_REG_RSP)==sp+8
        actual=bytearray(m.mem_read(vm,0x120))
        for p in [0xf0,0xf8]:
            value=struct.unpack_from('<Q',actual,p)[0]
            if value:
                base=next(lo for lo,hi in ranges if lo<=value<hi);struct.pack_into('<Q',actual,p,value-base)
        value=struct.unpack_from('<Q',actual,0x100)[0]
        if value:struct.pack_into('<Q',actual,0x100,(value-manager-0x608)//64+1)
        wanted=bytes.fromhex(slot['state']);diff=[hex(i) for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b]
        assert not diff,(slot['id'],diff);digest.update(actual)
    sources=['shared/th06nc/title-layout.mjs','shared/th06nc/title-animations.mjs','shared/th06nc/anm-bank.mjs','shared/th06nc/anm-vm.mjs']
    report=dict(scope=__doc__,executableSha256=target['sha256'],sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},resources=9,slots=len(expected['slots']),stateSha256=digest.hexdigest(),passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
