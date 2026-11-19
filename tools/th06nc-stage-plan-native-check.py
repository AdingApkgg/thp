"""Stage enemy/ECL resource plan from original tables and setup call sites.

Records successful resource API arguments; allocation, texture loading and
complete stage creation are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    plans=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{stageAssetPlan}from'./shared/th06nc/stage-layout.mjs';console.log(JSON.stringify(Array.from({length:7},(_,i)=>stageAssetPlan(i+1))));"],cwd=ROOT));n=Native();m=n.m;calls=[]
    def string(p):return bytes(m.mem_read(p,128)).split(b'\0')[0].decode()if p else None
    def hook(m,a,size,u):
        if a not in [0x140037170,0x1400387a0,0x1400020b0]:return
        if a==0x140037170:calls.append(dict(primary=string(m.reg_read(UC_X86_REG_RCX)),secondary=string(m.reg_read(UC_X86_REG_RDX))));retvalue=0
        elif a==0x1400387a0:calls.append(dict(ecl=string(m.reg_read(UC_X86_REG_RCX))));retvalue=n.assets
        else:calls.append(dict(file=string(m.reg_read(UC_X86_REG_R8)),slot=m.reg_read(UC_X86_REG_RDX),base=m.reg_read(UC_X86_REG_R9)));retvalue=0
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,retvalue)
    m.hook_add(UC_HOOK_CODE,hook)
    for p in plans:
        calls.clear();m.mem_write(n.owner+0x24,struct.pack('<i',p['stage']));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_RSI,0x140000000);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003b38b,0x14003b3d8,count=10000)
        assert calls==[dict(primary='data/'+p['enemyAnimations'][0]['file'],secondary='data/'+p['enemyAnimations'][1]['file']if len(p['enemyAnimations'])>1 else None),dict(ecl='data/'+p['ecl'])],(p,calls)
        # Direct fast setup path chooses slot 8 then optional 9, base 0x100.
        m.mem_write(n.vm,('data/'+p['enemyAnimations'][0]['file']+'\0').encode());m.mem_write(n.vm+128,('data/'+p['enemyAnimations'][-1]['file']+'\0').encode())
        # Setup's large owner is global storage, with resource names at +10c0c0.
        owner=0x140a6de90;m.mem_write(owner+0x10c0c0,struct.pack('<QQ',n.vm,n.vm+128 if len(p['enemyAnimations'])>1 else 0));calls.clear()
        m.reg_write(UC_X86_REG_RBX,owner);m.reg_write(UC_X86_REG_RDI,0);m.reg_write(UC_X86_REG_RBP,9);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000)
        m.emu_start(0x140037264,0x1400372c5,count=10000)
        assert calls==[dict(file='data/'+r['file'],slot=r['slot'],base=r['base'])for r in p['enemyAnimations']],(p,calls)
    report=dict(scope=__doc__,stages=7,plans=plans,sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/stage-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-stage-plan-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='plans'}))
if __name__=='__main__':main()
