"""Active bullet motion 10ab5..11060: acceleration, turns and wall bounces.

Full bullet bytes compared with shared trig values. Appearance, culling,
collision, ANM tick and final timer are outside this focused check.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/bullet-motion.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';import{advanceBulletMotion}from'./shared/th06nc/bullet-motion.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const pool=new BulletPool({anmBank:bank}),d=new Uint8Array(108),dv=new DataView(d.buffer);dv.setInt16(0x18,1,true);dv.setInt16(0x1a,1,true);pool.spawn(d);const entry=pool.entry(0),initial=entry.bytes.slice(),cases=[];
for(const flags of [0,1,16,32,64,128,256,512,1024,2048,17,33,48,192,320,1152,3072,4095])for(const clock of [0,16,17,29,30,59,60,61,100])for(const position of [[100,100],[-20,100],[-8,100],[384,100],[400,100],[100,-20],[100,448],[100,470],[-20,-20],[400,470]]){
 entry.bytes.set(initial);const v=entry.v;v.setUint16(0x14,flags,true);v.setInt32(0x2c,clock,true);v.setInt32(0x48,30,true);v.setFloat32(8,1.25,true);v.setFloat32(0xc,-0.75,true);v.setFloat32(0x10,0.125,true);v.setFloat32(0x24,3.7,true);v.setFloat32(0x40,0.5,true);v.setFloat32(0x18,0.1,true);v.setFloat32(0x600,0.02,true);v.setFloat32(0x608,0.1,true);v.setFloat32(0x60c,-0.2,true);v.setFloat32(0x610,0.01,true);v.setFloat32(0x614,0.4,true);v.setFloat32(0,2.5,true);v.setInt32(4,30,true);v.setInt32(0x1c,1,true);v.setInt32(0x20,3,true);v.setFloat32(0x30,position[0],true);v.setFloat32(0x34,position[1],true);const before=hex(entry.bytes);advanceBulletMotion(entry,{sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,playerPosition:[192,400,0]});cases.push({flags,clock,position,before,after:hex(entry.bytes)});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m
    def hook(m,a,size,u):
        value=0.875 if a==0x1402be065 else 0.75 if a==0x1402be071 else 0.25;m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be065,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    digest=hashlib.sha256();m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0))
    for index,c in enumerate(data['cases']):
        before=bytearray.fromhex(c['before']);ptr=struct.unpack_from('<Q',before,0x150)[0];struct.pack_into('<Q',before,0x150,n.manager+0x608+(ptr-1)*64);m.mem_write(n.vm,bytes(before))
        for reg,value in [(UC_X86_REG_RBX,n.vm),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R12D,1),(UC_X86_REG_R13D,0),(UC_X86_REG_R8D,0xffef),(UC_X86_REG_R9D,0xffdf)]:m.reg_write(reg,value)
        for reg,value in [(UC_X86_REG_XMM1,5),(UC_X86_REG_XMM6,-0.0),(UC_X86_REG_XMM8,384),(UC_X86_REG_XMM9,448),(UC_X86_REG_XMM10,3.141592653589793),(UC_X86_REG_XMM11,-3.141592653589793),(UC_X86_REG_XMM12,0),(UC_X86_REG_XMM13,-6.283185307179586),(UC_X86_REG_XMM14,6.283185307179586),(UC_X86_REG_XMM15,0.5)]:m.reg_write(reg,int.from_bytes(struct.pack('<f',value),'little'))
        m.emu_start(0x140010ab5,0x140011060,count=100000);actual=bytearray(m.mem_read(n.vm,0x620));struct.pack_into('<Q',actual,0x150,ptr);wanted=bytes.fromhex(c['after'])
        assert actual==wanted,(index,c['flags'],c['clock'],c['position'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-bullet-motion-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
