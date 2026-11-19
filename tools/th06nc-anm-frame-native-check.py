"""Direct original post-command ANM ticks versus portable frame integration.

States come from the independently checked retail command corpus. This does not
cover command scheduling, interrupts, sprite selection, draw calls or pixels.
"""
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_R11,UC_X86_REG_RDI,UC_X86_REG_RSP,UC_X86_REG_XMM5,UC_X86_REG_XMM6,UC_X86_REG_XMM7

ROOT=Path(__file__).resolve().parents[1]


def main():
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes())
    blob=Path(target['executable']).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==target['sha256']
    machine=Uc(UC_ARCH_X86,UC_MODE_64);machine.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(blob):machine.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    machine.mem_map(0x70000000,0x20000)
    home=ROOT/'artifacts/th06nc'
    inputs=json.loads((home/'anm-command-native-cases.json').read_bytes())
    cases=[]
    for index,source in enumerate(inputs):
        state=bytes.fromhex(source['expected'])
        expected=[]
        machine.mem_write(0x70000000,state)
        for tick in range(4):
            machine.reg_write(UC_X86_REG_R11,0x70000000);machine.reg_write(UC_X86_REG_RDI,0)
            machine.reg_write(UC_X86_REG_RSP,0x70018000)
            machine.reg_write(UC_X86_REG_XMM5,0x3f800000);machine.reg_write(UC_X86_REG_XMM6,0);machine.reg_write(UC_X86_REG_XMM7,0xbf800000)
            machine.emu_start(0x140006e0a,0x140007470,count=10000)
            expected.append(bytes(machine.mem_read(0x70000000,0x120)).hex())
        cases.append(dict(source=index,initial=state.hex(),expected=expected))
    path=home/'anm-frame-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import {readFileSync} from 'node:fs';import assert from 'node:assert/strict';import {advanceAnmFrame} from './shared/th06nc/anm-frame.mjs';
const cases=JSON.parse(readFileSync('artifacts/th06nc/anm-frame-native-cases.json'));let count=0;
for(const c of cases){const state=Buffer.from(c.initial,'hex');for(const [tick,expected]of c.expected.entries()){advanceAnmFrame(state);assert.equal(state.toString('hex'),expected,`source ${c.source} tick ${tick}`);count++;}}console.log(count+' native frame ticks agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,executableSha256=target['sha256'],readerSha256=hashlib.sha256((ROOT/'shared/th06nc/anm-frame.mjs').read_bytes()).hexdigest(),sourceStates=len(cases),ticks=len(cases)*4,comparedBytes=len(cases)*4*288,casesSha256=hashlib.sha256(path.read_bytes()).hexdigest(),nativeRange=['0x140006e0a','0x140007470'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-frame-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
