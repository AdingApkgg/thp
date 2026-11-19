"""Item draw 11b0a..11c2a: normal sprites, above-screen arrows, alpha and order.

Whole item pool and 2D draw calls compared; GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/item-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{ItemPool}from'./shared/th06nc/item-pool.mjs';import{drawItems}from'./shared/th06nc/item-draw.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[],hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});for(const y of [-200,-136,-120,-9,-8,-7,0,200])for(const normal of [false,true])for(const active of [false,true]){
 const pool=new ItemPool({anmBank:bank});for(let type=0;type<7;type++){const e=pool.spawn({type,mode:1,position:[100+type*20,y,.5]});e.v.setUint8(0,active?1:0);e.v.setUint8(0x158,normal?1:0);if(!normal)e.vm.bindSprite(0x207+type);e.vm.v.setUint32(0xec,0x89abcdef,true);}const before=hex(pool.storage.subarray(0,7*0x160)),calls=[];drawItems(pool,(vm,info)=>calls.push({...info,state:hex(vm.state)}));cases.push({before,calls,sha256:createHash('sha256').update(pool.storage).digest('hex')});}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;calls=[];digest=hashlib.sha256();base=0x140baf0d8
    def normalize(block,offset,encode=False):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:struct.pack_into('<Q',block,p,n.assetByFile['etama3.anm']+ptr if encode else ptr-n.assetByFile['etama3.anm'])
        p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
        if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        ptr=m.reg_read(UC_X86_REG_RDX);state=bytearray(m.mem_read(ptr,288));normalize(state,0);calls.append(dict(snap=bool(m.reg_read(UC_X86_REG_R8B)),space='screen',part='item',slot=(ptr-base)//0x160,state=state.hex()));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1400067f0,end=0x1400067f0)
    for index,c in enumerate(data['cases']):
        state=bytearray.fromhex(c['before'])
        for slot in range(7):normalize(state,slot*0x160+0x38,True)
        m.mem_write(base,bytes(1025*0x160));m.mem_write(base,bytes(state));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_R12D,0);m.reg_write(UC_X86_REG_R14D,64);calls.clear();m.emu_start(0x140011b0a,0x140011c2a,count=1000000);assert calls==c['calls'],(index,'calls',calls[:1],c['calls'][:1]);actual=bytearray(m.mem_read(base,1025*0x160))
        for slot in range(7):normalize(actual,slot*0x160+0x38)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'pool');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),drawCalls=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-item-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
