"""Actual 426e0 shared item constructor, all seven types and three drop modes.

Practice filtering, full-pool/wrap cases and death scatter compare complete
pool bytes, allocation cursor and shared RNG. Update/pickup/GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/item-pool.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{ItemPool}from'./shared/th06nc/item-pool.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(let type=0;type<7;type++)for(const mode of [0,1,2])for(const practice of [false,true])for(const occupied of [0,1023,1024])for(const start of [0,1023])for(const x of [-16,0,8,192,376,400]){
 const rng=new NativeRng(0xbeef,99),pool=new ItemPool({anmBank:bank,environment:{rng,spellPractice:practice}});pool.cursor=start;for(let slot=0;slot<occupied;slot++)pool.entry(slot).v.setUint8(0,1);const result=pool.spawn({type,mode,position:[x,100,0.5]});cases.push({type,mode,practice,occupied,start,x,slot:result?.slot??null,cursor:pool.cursor,rng,sha256:createHash('sha256').update(pool.storage).digest('hex')});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x140baf0d8;size=1025*0x160;digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        initial=bytearray(size)
        for slot in range(c['occupied']):initial[slot*0x160]=1
        m.mem_write(base,bytes(initial));m.mem_write(0x140c07238,struct.pack('<i',c['start']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f27b5,bytes([c['practice']]));m.mem_write(n.vm,struct.pack('<3f',c['x'],100,0.5));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8D,c['type']);m.reg_write(UC_X86_REG_R9D,c['mode']);m.emu_start(0x1400426e0,n.stack+0xf000,count=1000000);actual=bytearray(m.mem_read(base,size))
        if c['slot']is not None:
            offset=c['slot']*0x160+0x38
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'pool',c);assert struct.unpack('<i',m.mem_read(0x140c07238,4))[0]==c['cursor'],(index,'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-item-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
