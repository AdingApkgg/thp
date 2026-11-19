"""Text startup and HUD message resource bases/slots from actual setup code.

All seven stages and both characters. Observes loaders in 7a817 and
3d500..3db35; excludes unrelated HUD resources and message file I/O.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/message-layout.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{messageAssetPlan}from'./shared/th06nc/message-layout.mjs';const cases=[];for(let stage=1;stage<=7;stage++)for(let character=0;character<2;character++)cases.push({stage,character,refs:messageAssetPlan(stage,character)});console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;calls=[];files=json.loads((ROOT/'artifacts/th06nc/scripts.json').read_bytes());archives={f['name']:f['archive']for f in files};digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400020b0:
            file=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),64)).split(b'\0')[0].decode().split('/')[-1];calls.append(dict(archive=archives[file],file=file,slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_EAX,0)
        else:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400020b0,0x1402bdee2]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.mem_write(0x140a6e9b0,struct.pack('<Q',n.manager));m.mem_write(0x140c21d9c,bytes(4))
    for c in cases:
        calls.clear();m.mem_write(0x1404f1e84,struct.pack('<i',c['stage']));m.mem_write(0x1404f1e80,bytes([c['character'],0]));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007a817,0x14007a82b,count=100000);m.reg_write(UC_X86_REG_RCX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003d500,0x14003db35,count=1000000);actual=[r for r in calls if r['file']=='text.anm'or r['file']=='msgframe.anm'or r['file'].startswith('face')];assert actual==c['refs'],(c['stage'],c['character'],actual,c['refs']);digest.update(json.dumps(actual,sort_keys=True).encode())
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-message-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
