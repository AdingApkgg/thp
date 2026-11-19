"""Original 4dc0 uncropped world vertices/UV, before GPU submission.

Actual manager corner initialization runs. Shared trig values isolate geometry;
camera, clipping, sampling and pixel equivalence are outside this check.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/anm-world-quad.mjs']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{LaserPool}from'./shared/th06nc/laser-pool.mjs';import{anmWorldQuad}from'./shared/th06nc/anm-world-quad.mjs';
const refs=commonProjectileAssetPlan(),bank=new AnmBank(),hex=b=>Buffer.from(b.buffer,b.byteOffset,b.byteLength).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const pool=new LaserPool({anmBank:bank}),descriptor=new Uint8Array(68);descriptor[0x2c]=1;pool.spawn(descriptor);const cases=[];
for(const part of ['main','end'])for(let anchor=0;anchor<8;anchor++)for(const scale of [-2,0,0.5,3])for(const axis of [-1,0,1,2,3]){
 const vm=pool.entry(0)[part],v=vm.v;v.setUint32(0xc4,3|(anchor<<8),true);v.setFloat32(0xc8,123.25,true);v.setFloat32(0xcc,234.5,true);v.setFloat32(0xd0,-1.5,true);v.setFloat32(0xe8,scale,true);v.setFloat32(0xe4,scale*2,true);v.setFloat32(0x2c,0.125,true);v.setFloat32(0x30,-0.25,true);for(let k=0;k<3;k++)v.setFloat32(0x9c+k*4,axis===k||axis===3?0.5:0,true);
 cases.push({part,state:hex(vm.state),expected:hex(anmWorldQuad(vm,{sin:()=>0.25,cos:()=>0.75}))});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m
    m.reg_write(UC_X86_REG_RDI,0);m.emu_start(0x14007a863,0x14007a8fe,count=10000)
    def hook(m,a,size,u):
        value=0.25 if a==0x1402bdf48 else 0.75
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<d',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdf48,0x1402bdf30]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        state=bytearray.fromhex(c['state']);ptr=struct.unpack_from('<Q',state,0x100)[0];struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64);m.mem_write(n.vm,bytes(state))
        m.mem_write(n.manager+0x20f84,bytes([0,0,3]));m.mem_write(n.manager+0x20f80,bytes(4));m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000)
        m.emu_start(0x140004dc0,0x140005978,count=100000)
        actual=b''.join(bytes(m.mem_read(0x140a6e9c0+i*0x30,12))+bytes(m.mem_read(0x140a6e9e0+i*0x30,8))for i in range(4));wanted=bytes.fromhex(c['expected'])
        assert actual==wanted,(index,c['part'],struct.unpack('<20f',actual),struct.unpack('<20f',wanted));digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-world-quad-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
