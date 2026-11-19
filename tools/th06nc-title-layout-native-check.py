"""Execute title initializer instruction regions to observe resource and VM calls.

External resource loading and VM setter calls are observed at their entry then
returned successfully; this checks arguments/order, not the skipped operations.
"""
import hashlib,importlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RBX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_R15,UC_X86_REG_R14,UC_X86_REG_R12,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RIP
ROOT=Path(__file__).resolve().parents[1]


def main():
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());b=Path(target['executable']).read_bytes();assert hashlib.sha256(b).hexdigest()==target['sha256']
    m=Uc(UC_ARCH_X86,UC_MODE_64);m.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(b):m.mem_write(0x140000000+s['va'],b[s['raw']:s['raw']+s['rawsize']])
    owner,stack=0x70000000,0x71000000;m.mem_map(owner,0x20000);m.mem_map(stack,0x10000)
    events=[]
    def hook(m,address,size,user):
        if address not in [0x1400020b0,0x140002760,0x140046dc0]:return
        if address==0x1400020b0:
            ptr=m.reg_read(UC_X86_REG_R8);name=bytes(m.mem_read(ptr,128)).split(b'\0')[0].decode()
            events.append(dict(kind='load',file=name.split('/')[-1],slot=m.reg_read(UC_X86_REG_RDX)&0xffffffff,base=m.reg_read(UC_X86_REG_R9)&0xffffffff))
        else:
            ptr=m.reg_read(UC_X86_REG_RDX if address==0x140002760 else UC_X86_REG_RCX)
            ident=m.reg_read(UC_X86_REG_R8 if address==0x140002760 else UC_X86_REG_RDX)&0xffffffff
            events.append(dict(kind='vm',offset=ptr-owner,id=ident))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook)
    reports=[]
    for disabled in [bytes(0x7d),bytes(i%3==0 for i in range(0x7d))]:
        events.clear();m.mem_write(owner,bytes(0x20000));m.mem_write(owner+0x158e0,disabled)
        for reg,val in [(UC_X86_REG_RSI,owner),(UC_X86_REG_RDI,owner+0x158e0),(UC_X86_REG_R15,0x100),(UC_X86_REG_R12,0x1c),(UC_X86_REG_R14,0x18),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,stack+0x8000)]:m.reg_write(reg,val)
        m.emu_start(0x140047b88,0x140047ccb,count=100000)
        m.emu_start(0x140047d1e,0x140047e1b,count=100000)
        script="import {titleResources,titleVmSlots}from'./shared/th06nc/title-layout.mjs';console.log(JSON.stringify({loads:titleResources,vms:titleVmSlots(Uint8Array.from(JSON.parse(process.argv[1])))}));"
        expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',script,json.dumps(list(disabled))],cwd=ROOT))
        loads=[{k:v for k,v in e.items() if k!='kind'} for e in events if e['kind']=='load'];vms=[{k:v for k,v in e.items() if k!='kind'} for e in events if e['kind']=='vm']
        assert loads==expected['loads'];assert vms==expected['vms'],(vms,expected['vms'])
        reports.append(dict(disabled=list(disabled),loads=loads,vmSlots=vms))
    report=dict(scope=__doc__,executableSha256=target['sha256'],sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-layout.mjs').read_bytes()).hexdigest(),cases=reports,passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Two title resource/VM layout cases agree')


if __name__=='__main__':main()
