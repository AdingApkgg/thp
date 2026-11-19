"""Original XY/UV calculations on title VM states, including rotated crops.

Compares geometry only, without draw submission, sampling, blend or pixels.
Rotated cases supply identical f32 sine/cosine to both geometry paths; native
CRT trigonometry is outside this check.
"""
import hashlib,importlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RBX,UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_R14,UC_X86_REG_R15,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RDX,UC_X86_REG_XMM12,UC_X86_REG_XMM0
ROOT=Path(__file__).resolve().parents[1]


def main():
    subprocess.run(['node','tools/th06nc-anm-vm-cases.mjs'],cwd=ROOT,check=True)
    subprocess.run(['node','tools/th06nc-anm-quad-cases.mjs'],cwd=ROOT,check=True)
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());blob=Path(target['executable']).read_bytes();assert hashlib.sha256(blob).hexdigest()==target['sha256']
    m=Uc(UC_ARCH_X86,UC_MODE_64);m.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(blob):m.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    asset,manager,stack,vm=0x70000000,0x71000000,0x72000000,0x73000000
    for addr,size in [(asset,0x100000),(manager,0x40000),(stack,0x10000),(vm,0x10000)]:m.mem_map(addr,size)
    cases=json.loads((ROOT/'artifacts/th06nc/anm-quad-cases.json').read_bytes());last=None;digest=hashlib.sha256()
    for c in cases:
        if c['path']!=last:
            m.mem_write(asset,Path(c['path']).read_bytes());m.mem_write(manager,bytes(0x40000));m.mem_write(manager+8,struct.pack('<Q',asset))
            for reg,val in [(UC_X86_REG_RBX,manager),(UC_X86_REG_RDI,asset),(UC_X86_REG_RSI,0),(UC_X86_REG_R14,0),(UC_X86_REG_R15,0),(UC_X86_REG_RBP,stack+0x8100),(UC_X86_REG_RSP,stack+0x8000)]:m.reg_write(reg,val)
            m.emu_start(0x1400024ae,0x14000270b,count=1000000);last=c['path']
        state=bytearray.fromhex(c['state']);ident=struct.unpack_from('<H',state,0x34)[0];struct.pack_into('<Q',state,0x100,manager+0x608+ident*64)
        m.mem_write(vm,bytes(state));m.mem_write(0x140c21e48,struct.pack('<I',c['height']));m.reg_write(UC_X86_REG_RDX,vm)
        if c['angle']:
            m.reg_write(UC_X86_REG_RBX,vm);m.reg_write(UC_X86_REG_RDI,manager);m.reg_write(UC_X86_REG_RSI,0);m.reg_write(UC_X86_REG_RSP,stack+0x8000)
            for reg,key in [(UC_X86_REG_XMM12,'sin'),(UC_X86_REG_XMM0,'cos')]:m.reg_write(reg,struct.unpack('<I',struct.pack('<f',c[key]))[0])
            m.emu_start(0x1400037a5,0x140003af1,count=10000)
        else:m.emu_start(0x140002ba1,0x140002e05,count=10000)
        actual=b''.join(bytes(m.mem_read(0x140a6ec70+j*24,8))+bytes(m.mem_read(0x140a6ec80+j*24,8)) for j in range(4))
        wanted=bytes.fromhex(c['expected']);assert actual==wanted,(c['name'],c['id'],c['frame'],c['height'],struct.unpack('<16f',actual),struct.unpack('<16f',wanted))
        digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),rotatedCases=sum(bool(c['angle']) for c in cases),rotatedCropCases=sum(bool(c.get('cropped')) for c in cases),heights=sorted({c['height'] for c in cases}),comparedBytes=len(cases)*64,stateSha256=digest.hexdigest(),readerSha256=hashlib.sha256((ROOT/'shared/th06nc/anm-quad.mjs').read_bytes()).hexdigest(),executableSha256=target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    report['sourceSha256']={'shared/th06nc/anm-quad.mjs':report['readerSha256']}
    (ROOT/'docs/porting/th06nc-anm-quad-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
