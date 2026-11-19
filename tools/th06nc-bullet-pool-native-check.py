"""Ordinary bullet constructor f870 and real ten-template ANM initialization.

Full pool bytes, allocation cursor, RNG and sound slots are compared. Shared
trig inputs isolate construction; movement, draw and player contact excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/bullet-pool.mjs','shared/th06nc/bullet-pattern.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),hash=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const make=()=>new BulletPool({anmBank:bank,environment:{rng:new NativeRng(0xbeef,99),playerPosition:[192,400,0]},sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,soundSlots:[-1,7,-1]}),templates=make().templates.map(t=>hash(t.bytes)),cases=[];
for(let type=0;type<10;type++)for(const color of [0,1,5,7])for(const flags of [0,2,4,8,16,32,64,128,256,512,1024,2048,4095])for(const occupied of [0,639,640]){
 const pool=make(),bytes=new Uint8Array(108),v=new DataView(bytes.buffer);v.setUint16(0,flags,true);v.setFloat32(4,3.7,true);v.setFloat32(8,0.4,true);v.setFloat32(0xc,100,true);v.setFloat32(0x10,200,true);v.setInt16(0x18,3,true);v.setInt16(0x1a,2,true);v.setInt32(0x1c,60,true);v.setInt32(0x20,4,true);v.setInt16(0x2c,type,true);v.setInt16(0x2e,color,true);v.setInt16(0x30,(type+color)%9,true);v.setFloat32(0x34,0.5,true);v.setFloat32(0x38,0.6,true);v.setInt32(0x3c,14,true);v.setFloat32(0x40,0.1,true);v.setFloat32(0x44,-1000,true);for(let i=0;i<occupied;i++)pool.entry(i).v.setUint16(0x44,1,true);pool.cursor=637;const result=pool.spawn(bytes);cases.push({descriptor:Buffer.from(bytes).toString('hex'),occupied,slots:result.map(x=>x.slot),cursor:pool.cursor,rng:pool.environment.rng,sound:pool.soundSlots,sha256:hash(pool.storage),first:result.length?Buffer.from(result[0].bytes).toString('hex'):null});
}console.log(JSON.stringify({refs,templates,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x1403ec2a0;poolBase=base+8;poolSize=640*0x620
    m.reg_write(UC_X86_REG_RBX,base);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140011fee,0x140012329,count=1000000)
    def normalize(block,offset):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:
                asset=next(a for a,b in n.ranges if a<=ptr<b);struct.pack_into('<Q',block,p,ptr-asset)
        p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
        if ptr:struct.pack_into('<Q',block,p,(ptr-n.manager-0x608)//64+1)
    for i,wanted in enumerate(data['templates']):
        block=bytearray(m.mem_read(base+0xff620+i*0x5b0,0x5b0))
        for j in range(5):normalize(block,j*0x120)
        assert hashlib.sha256(block).hexdigest()==wanted,('template',i)
    def hook(m,a,size,u):
        value=0.875 if a==0x1402be065 else 0.75 if a==0x1402be071 else 0.25;m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be065,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        initial=bytearray(poolSize)
        for slot in range(c['occupied']):struct.pack_into('<H',initial,slot*0x620+0x44,1)
        m.mem_write(poolBase,bytes(initial));m.mem_write(base+0xff618,struct.pack('<i',637));m.mem_write(n.vm,bytes.fromhex(c['descriptor']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x140509670,struct.pack('<3i',-1,7,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404f27b5,b'\0');sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,base);m.reg_write(UC_X86_REG_RDX,n.vm);m.emu_start(0x14000f870,n.stack+0xf000,count=1000000)
        actual=bytearray(m.mem_read(poolBase,poolSize))
        for slot in c['slots']:
            for j in range(5):normalize(actual,slot*0x620+0x50+j*0x120)
        
        if hashlib.sha256(actual).hexdigest()!=c['sha256']:
            wanted=bytes.fromhex(c['first']);got=actual[c['slots'][0]*0x620:(c['slots'][0]+1)*0x620];raise AssertionError((index,'pool',[(hex(p),a,b)for p,(a,b)in enumerate(zip(got,wanted))if a!=b][:40]))
        assert struct.unpack('<i',m.mem_read(base+0xff618,4))[0]==c['cursor'],(index,'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sound'],(index,'sound');digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(data['cases']),templates=10,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-bullet-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
