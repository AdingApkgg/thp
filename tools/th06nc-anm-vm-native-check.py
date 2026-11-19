"""Complete original ANM updater versus portable VM on retail title scripts.

Headless state comparison from shared initialized states, not original game
rendering, startup/setter acceptance or title lifecycle. Script and sprite
pointers are normalized to file offsets and local sprite IDs for comparison.
"""
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP,UC_X86_REG_RBX,UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_R14,UC_X86_REG_R15,UC_X86_REG_RBP,UC_X86_REG_RAX

ROOT=Path(__file__).resolve().parents[1]


def main():
    subprocess.run(['node','tools/th06nc-anm-vm-cases.mjs'],cwd=ROOT,check=True)
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes())
    blob=Path(target['executable']).read_bytes();assert hashlib.sha256(blob).hexdigest()==target['sha256']
    machine=Uc(UC_ARCH_X86,UC_MODE_64);machine.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(blob):machine.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    asset,manager,stack,vm=0x70000000,0x71000000,0x72000000,0x73000000
    for addr,size in [(asset,0x100000),(manager,0x40000),(stack,0x10000),(vm,0x10000)]:machine.mem_map(addr,size)
    cases=json.loads((ROOT/'artifacts/th06nc/anm-vm-cases.json').read_bytes());ticks=0;digest=hashlib.sha256()
    for case in cases:
        b=Path(case['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==case['sha256']
        machine.mem_write(asset,b);machine.mem_write(manager,bytes(0x40000));machine.mem_write(manager+8,struct.pack('<Q',asset))
        for reg,val in [(UC_X86_REG_RBX,manager),(UC_X86_REG_RDI,asset),(UC_X86_REG_RSI,0),(UC_X86_REG_R14,0),(UC_X86_REG_R15,0),(UC_X86_REG_RBP,stack+0x8100),(UC_X86_REG_RSP,stack+0x8000)]:machine.reg_write(reg,val)
        machine.emu_start(0x1400024ae,0x14000270b,count=1000000)
        initial=bytearray.fromhex(case['initial'])
        for p in [0xf0,0xf8]:struct.pack_into('<Q',initial,p,asset+struct.unpack_from('<Q',initial,p)[0])
        machine.mem_write(vm,bytes(initial))
        for tick,expected in enumerate(case['frames']):
            if expected['interrupt']:machine.mem_write(vm+0x8a,struct.pack('<h',expected['interrupt']))
            sp=stack+0x8008;machine.mem_write(sp,struct.pack('<Q',stack))
            machine.reg_write(UC_X86_REG_RSP,sp);machine.reg_write(UC_X86_REG_RCX,manager);machine.reg_write(UC_X86_REG_RDX,vm)
            machine.emu_start(0x1400069b0,stack,count=1000000)
            assert machine.reg_read(UC_X86_REG_RSP)==sp+8,'native updater did not return'
            actual=bytearray(machine.mem_read(vm,0x120))
            for p in [0xf0,0xf8]:
                value=struct.unpack_from('<Q',actual,p)[0]
                if value:struct.pack_into('<Q',actual,p,value-asset)
            sprite=struct.unpack_from('<Q',actual,0x100)[0]
            if sprite:struct.pack_into('<Q',actual,0x100,(sprite-manager-0x608)//64+1)
            wanted=bytes.fromhex(expected['state'])
            differences=[hex(i) for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b]
            assert not differences,(case['name'],case['id'],tick,differences)
            assert machine.reg_read(UC_X86_REG_RAX)&0xffffffff==expected['result']
            ticks+=1;digest.update(actual)
    sources=['shared/th06nc/anm-vm.mjs','shared/th06nc/anm-command.mjs','shared/th06nc/anm-frame.mjs','shared/th06nc/anm.mjs','tools/th06nc-anm-vm-cases.mjs']
    report=dict(scope=__doc__,cases=len(cases),ticks=ticks,comparedBytes=ticks*288,requestedInterrupts=sum(bool(f['interrupt']) for c in cases for f in c['frames']),framesPerCase=360,executableSha256=target['sha256'],sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},stateSha256=digest.hexdigest(),passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-vm-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
