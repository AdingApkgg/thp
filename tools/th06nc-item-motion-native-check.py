"""Item movement block 42aef..42cb7: falling, POC homing and death scatter.

Player state/POC boundaries, scatter endpoint and offscreen removal compare
complete item bytes with shared trig. Pickup, ANM and final clock excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/item-motion.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{advanceItemMotion}from'./shared/th06nc/item-motion.mjs';const cases=[];for(const mode of [0,1,2])for(const playerState of [0,1,2,3,255])for(const playerPosition of [[192,100,0.5],[192,128,0.5],[192,400,0.5]])for(const clock of [0,30,59,60,61])for(const position of [[192,100,0.5],[100,100,0.5],[100,463,0.5]]){
 const bytes=new Uint8Array(0x160),v=new DataView(bytes.buffer);v.setUint8(0,1);v.setUint8(0xc,mode);v.setInt32(8,clock,true);position.forEach((x,k)=>v.setFloat32(0x10+k*4,x,true));[2,-4,0.25].forEach((x,k)=>v.setFloat32(0x1c+k*4,x,true));[200,-40,0].forEach((x,k)=>v.setFloat32(0x28+k*4,x,true));const before=Buffer.from(bytes).toString('hex'),result=advanceItemMotion({v},{playerPosition,playerState,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875});cases.push({mode,playerState,playerPosition,before,result,after:Buffer.from(bytes).toString('hex')});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x140043796:m.emu_stop();return
        value=0.875 if a==0x1402be065 else 0.75 if a==0x1402be071 else 0.25;m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be065,0x1402be071,0x1402be07d,0x140043796]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x140506c38,bytes([c['playerState']]));m.mem_write(0x140506ad0,struct.pack('<3f',*c['playerPosition']))
        for reg,value in [(UC_X86_REG_R14,n.owner),(UC_X86_REG_R12,n.owner+0x1c),(UC_X86_REG_R13,n.owner+0x10),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        for reg,value in [(UC_X86_REG_XMM0,60),(UC_X86_REG_XMM1,1),(UC_X86_REG_XMM7,0),(UC_X86_REG_XMM8,8),(UC_X86_REG_XMM9,1.5707963267948966),(UC_X86_REG_XMM10,-2.2),(UC_X86_REG_XMM11,128),(UC_X86_REG_XMM13,0.03),(UC_X86_REG_XMM14,3),(UC_X86_REG_XMM15,464)]:m.reg_write(reg,int.from_bytes(struct.pack('<f',value),'little'))
        m.emu_start(0x140042aef,0x140042cb7,count=100000);actual=bytes(m.mem_read(n.owner,0x160));wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,c['mode'],c['playerState'],c['playerPosition'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b]);assert bool(actual[0])==c['result'];digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-item-motion-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
