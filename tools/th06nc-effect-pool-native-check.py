"""Effect spawn helper: all 21 types, circular allocation, reuse and exhaustion.

Original helper and ANM binding/tick execute. Complete pool bytes, allocation
cursor, returned slot and RNG are compared. Effect callbacks/drawing excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{EffectPool,effectBytes}from'./shared/th06nc/effect-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const refs=[{file:'etama4.anm',archive:'th06CM.dat',base:698,slot:7},{file:'eff01.anm',archive:'th06ST.dat',base:723,slot:11}],bank=new AnmBank(),cases=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(let type=0;type<21;type++)for(const count of [1,3,0])for(const cursor of [0,511])for(const occupied of [0,1,512]){
 const rng=new NativeRng(0xbeef,99),pool=new EffectPool({anmBank:bank,rng});pool.cursor=cursor;
 for(let i=0;i<513;i++){const v=pool.entry(i).v;v.setFloat32(0x18,1.25,true);v.setFloat32(0x1c,2.5,true);v.setFloat32(0x20,3.75,true);v.setFloat32(0x184,4.5,true);v.setInt32(0x28,17,true);v.setUint32(0x104,0x1234,true);if(i<512&&(occupied===512||(occupied===1&&i===cursor)))v.setUint8(0x14,1);}
 const request={type,position:[100.5,200.25,-2],count,color:0x89abcdef},result=pool.spawn(request);cases.push({request,cursor,occupied,result:result.slot,afterCursor:pool.cursor,sha256:createHash('sha256').update(pool.storage).digest('hex'),rng:{seed:rng.seed,count:rng.count}});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x140a6ecd0;cursorAddress=0x140aa1e6c;digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        raw=bytearray(513*0x198)
        for slot in range(513):
            p=slot*0x198;struct.pack_into('<3f',raw,p+0x18,1.25,2.5,3.75);struct.pack_into('<f',raw,p+0x184,4.5);struct.pack_into('<i',raw,p+0x28,17);struct.pack_into('<I',raw,p+0x104,0x1234)
            if slot<512 and(c['occupied']==512 or(c['occupied']==1 and slot==c['cursor'])):raw[p+0x14]=1
        m.mem_write(base,bytes(raw));m.mem_write(cursorAddress,struct.pack('<i',c['cursor']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(n.vm,struct.pack('<3f',*c['request']['position']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<I',c['request']['color']))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_EDX,c['request']['type']),(UC_X86_REG_R8,n.vm),(UC_X86_REG_R9D,c['request']['count'])]:m.reg_write(reg,value)
        m.emu_start(0x14002b0d0,n.stack+0xf000,count=10000000);assert (m.reg_read(UC_X86_REG_RAX)-base)//0x198==c['result'],(index,'result');assert struct.unpack('<i',m.mem_read(cursorAddress,4))[0]==c['afterCursor'],(index,'cursor');actual=bytearray(m.mem_read(base,len(raw)))
        for slot in range(513):
            for offset in [0x130,0x138]:
                p=slot*0x198+offset;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:
                    resource=next(lo for lo,hi in n.ranges if lo<=ptr<hi);struct.pack_into('<Q',actual,p,ptr-resource)
            p=slot*0x198+0x140;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        actualHash=hashlib.sha256(actual).hexdigest();assert actualHash==c['sha256'],(index,c['request'],c['cursor'],c['occupied'],actualHash,c['sha256']);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),types=21,stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/effect-pool.mjs','shared/th06nc/anm-rebind.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-effect-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
