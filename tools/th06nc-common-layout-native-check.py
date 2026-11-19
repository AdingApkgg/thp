"""Shared projectile/effect ANM and stage effect resource API plans.

Original loader call sites execute with a successful resource API stub. Textures,
allocation and complete game resource initialization are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{commonProjectileAssetPlan,stageEffectAssetPlan}from'./shared/th06nc/common-layout.mjs';console.log(JSON.stringify({common:commonProjectileAssetPlan(),stages:Array.from({length:7},(_,i)=>stageEffectAssetPlan(i+1))}));"],cwd=ROOT));n=Native();m=n.m;calls=[]
    def hook(m,a,size,u):
        if a!=0x1400020b0:return
        calls.append(dict(file=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),64)).split(b'\0')[0].decode(),slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140011f92,0x140011fee,count=10000);assert calls==[dict(file='data/'+r['file'],slot=r['slot'],base=r['base'])for r in data['common']],calls
    for stage,r in enumerate(data['stages'],1):
        calls.clear();m.mem_write(0x1404f1e84,struct.pack('<i',stage));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.mem_write(n.stack+0x8028,struct.pack('<Q',n.stack+0xf000));m.emu_start(0x14002b3a1,n.stack+0xf000,count=10000);assert calls==[dict(file='data/'+r['file'],slot=r['slot'],base=r['base'])],(stage,calls,r)
    report=dict(scope=__doc__,common=data['common'],stages=data['stages'],sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/common-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-common-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['common','stages']}))
if __name__=='__main__':main()
