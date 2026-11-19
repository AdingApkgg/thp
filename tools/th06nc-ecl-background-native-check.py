"""ECL 125 direct background wait signal, native 284cf.

Compares the whole background/actor bytes after using the actual EnemyWorld
service wiring. Covers prior signal values; task scheduling is separate.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-command.mjs','shared/th06nc/enemy-world.mjs','shared/th06nc/spell-state.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EnemyWorld}from'./shared/th06nc/enemy-world.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex'),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata3.ecl'));for(const signal of [0,1,2,255]){const bytes=Uint8Array.from({length:0x220},(_,i)=>(i*17+signal)&255),initial=hex(bytes),background={v:new DataView(bytes.buffer)},world=new EnemyWorld(program,{anmBank:new AnmBank(),spellBackground:background}),enemy=Uint8Array.from({length:0x10b0},(_,i)=>i&255);applyEclCommand(enemy,{opcode:125,args:new Uint8Array()},world.services);cases.push({initial,after:hex(bytes),enemy:hex(enemy)});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for c in cases:
        m.mem_write(0x140509b60,bytes.fromhex(c['initial']));m.mem_write(n.owner,bytes.fromhex(c['enemy']));m.reg_write(UC_X86_REG_RDI,n.owner);m.emu_start(0x1400284cf,0x140025d7d,count=100);actual=bytes(m.mem_read(0x140509b60,0x220));assert actual.hex()==c['after'];assert bytes(m.mem_read(n.owner,0x10b0)).hex()==c['enemy'];digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-background-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
