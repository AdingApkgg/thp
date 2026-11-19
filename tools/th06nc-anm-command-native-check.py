"""Compare portable ANM command writes with original x64 switch bodies.

Single-command boundary only: excludes scheduler, sprite/RNG and interrupts.
"""
import base64
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
from unicorn.x86_const import UC_X86_REG_R11, UC_X86_REG_R10, UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_XMM5, UC_X86_REG_XMM6, UC_X86_REG_XMM7

ROOT=Path(__file__).resolve().parents[1]


def main():
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes())
    blob=Path(target['executable']).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==target['sha256']
    machine=Uc(UC_ARCH_X86,UC_MODE_64)
    machine.mem_map(0x140000000,0xd00000)
    sections=importlib.import_module('th-disasm').sections(blob)
    for s in sections:machine.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    sec=next(s for s in sections if s['va']<=0x7494<s['va']+s['rawsize'])
    dispatch=struct.unpack_from('<36I',blob,sec['raw']+0x7494-sec['va'])
    machine.mem_map(0x70000000,0x10000)
    # Use real command payloads, deduplicated by opcode and bytes.
    source="""
import {readFileSync} from 'node:fs';import {readAnm} from './shared/th06nc/anm.mjs';
const files=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.anm'));
const seen=new Map();for(const f of files)for(const s of readAnm(readFileSync(f.path)).scripts)for(const i of s.instructions){const args=Buffer.from(i.args).toString('base64');seen.set(i.opcode+':'+args,{opcode:i.opcode,args});}console.log(JSON.stringify([...seen.values()]));
"""
    commands=json.loads(subprocess.check_output(['node','--input-type=module','-e',source],cwd=ROOT))
    # These switch entries do not occur in this retail script corpus.
    commands += [dict(opcode=op,args='') for op in [6,8,33]]
    allowed=set(range(36))-{0,1,5,15,16,21,24}
    cases=[]
    for command in commands:
        op=command['opcode']
        if op not in allowed:continue
        args=base64.b64decode(command['args'])
        for flags in [0,0xffffffff]:
            initial=bytearray(struct.pack('<f',0.25)*72)
            struct.pack_into('<I',initial,0xc4,flags)
            machine.mem_write(0x70000000,bytes(initial))
            machine.mem_write(0x70001000,struct.pack('<hBB',0,op,len(args))+args)
            machine.reg_write(UC_X86_REG_R11,0x70000000)
            machine.reg_write(UC_X86_REG_R10,0x70001000)
            machine.reg_write(UC_X86_REG_RDI,0)
            machine.reg_write(UC_X86_REG_RDX,op)
            machine.reg_write(UC_X86_REG_XMM5,0x3f800000)
            machine.reg_write(UC_X86_REG_XMM6,0)
            machine.reg_write(UC_X86_REG_XMM7,0xbf800000)
            machine.emu_start(0x140000000+dispatch[op],0x1400070e3,count=10000)
            cases.append(dict(opcode=op,args=command['args'],initial=base64.b64encode(initial).decode(),expected=bytes(machine.mem_read(0x70000000,0x120)).hex()))
    home=ROOT/'artifacts/th06nc';home.mkdir(parents=True,exist_ok=True)
    path=home/'anm-command-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    driver="""
import {readFileSync} from 'node:fs';import assert from 'node:assert/strict';import {applyAnmCommand} from './shared/th06nc/anm-command.mjs';
const cases=JSON.parse(readFileSync('artifacts/th06nc/anm-command-native-cases.json'));
for(const [index,c]of cases.entries()){const state=Buffer.from(c.initial,'base64');applyAnmCommand(state,{opcode:c.opcode,args:Buffer.from(c.args,'base64')});assert.equal(state.toString('hex'),c.expected,`case ${index} opcode ${c.opcode}`);}console.log(cases.length+' native command cases agree');
"""
    subprocess.run(['node','--input-type=module','-e',driver],cwd=ROOT,check=True)
    report=dict(scope=__doc__,executableSha256=target['sha256'],commandReaderSha256=hashlib.sha256((ROOT/'shared/th06nc/anm-command.mjs').read_bytes()).hexdigest(),cases=len(cases),opcodes=sorted({c['opcode'] for c in cases}),comparedStateBytes=len(cases)*0x120,casesSha256=hashlib.sha256(path.read_bytes()).hexdigest(),passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-command-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
