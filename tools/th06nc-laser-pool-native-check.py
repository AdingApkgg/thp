"""Original laser constructor 105e0 with real common ANM resources.

Compares complete pool bytes, return handle and RNG across types/colors/aiming,
occupied/exhausted slots and practice suppression. Laser updates/drawing excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{LaserPool}from'./shared/th06nc/laser-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const type of [0,1])for(let color=0;color<16;color++)for(const aimed of [false,true])for(const occupied of [0,1,64])for(const delay of [0,5])for(const suppressed of [false,true]){
 const rng=new NativeRng(0xbeef,99),environment={rng,playerPosition:[192,400,0],spellPractice:true,spellFinished:suppressed},pool=new LaserPool({anmBank:bank,environment,atan2:()=>0.875}),descriptor=new Uint8Array(68),d=new DataView(descriptor.buffer);
 for(let p=0;p<68;p+=4)d.setFloat32(p,p/4+0.25,true);d.setInt16(0xc,type,true);d.setInt16(0xe,color,true);[100.5,200.25,-2].forEach((x,i)=>d.setFloat32(0x20+i*4,x,true));d.setUint8(0x2c,aimed?0:1);d.setInt32(0x30,delay,true);
 for(let i=0;i<65;i++){const v=pool.entry(i).v;v.setFloat32(0xe8,7.5,true);v.setFloat32(0x208,9.5,true);if(i<occupied)v.setUint8(0x274,1);}
 const result=pool.spawn(descriptor);cases.push({descriptor:Buffer.from(descriptor).toString('hex'),occupied,suppressed,result:result?result.slot:null,sha256:createHash('sha256').update(pool.storage).digest('hex'),rng:{seed:rng.seed,count:rng.count}});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;laserBase=0x1404e12b8;digest=hashlib.sha256()
    def hook(m,a,size,u):
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1402be065,end=0x1402be065)
    for index,c in enumerate(data['cases']):
        initial=bytearray(65*0x298)
        for i in range(65):struct.pack_into('<f',initial,i*0x298+0xe8,7.5);struct.pack_into('<f',initial,i*0x298+0x208,9.5);initial[i*0x298+0x274]=int(i<c['occupied'])
        m.mem_write(laserBase,bytes(initial));m.mem_write(n.vm,bytes.fromhex(c['descriptor']));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x140aa1e8e,bytes([c['suppressed']]));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.vm);m.emu_start(0x1400105e0,n.stack+0xf000,count=1000000)
        pointer=m.reg_read(UC_X86_REG_RAX);assert(None if pointer==0 else(pointer-laserBase)//0x298)==c['result'],(index,'result');actual=bytearray(m.mem_read(laserBase,len(initial)))
        for slot in range(65):
            for offset in [0x20,0x140]:
                for field in [0xf0,0xf8]:
                    p=slot*0x298+offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                p=slot*0x298+offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'pool',c['occupied'],c['descriptor']);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/laser-pool.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-laser-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
