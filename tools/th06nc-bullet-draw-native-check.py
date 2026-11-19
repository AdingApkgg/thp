"""Ordinary bullet owner draw passes, VM positions/rotation/tint and order.

Actual 11c2a..11f2d block with observed 2D draw calls. Pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/bullet-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';import{drawBullets}from'./shared/th06nc/bullet-draw.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const cases=[];
for(const state of [0,1,2,3,4,5,6])for(const rotate of [0,1]){
 const pool=new BulletPool({anmBank:bank}),entries=[],calls=[];
 for(let type=0;type<10;type++){const slot=type===9?639:40*type,entry=pool.entry(slot),v=entry.v;for(let j=0;j<5;j++){pool.copyAnm(entry,j,pool.templates[type]);entry.anms[j].v.setUint16(0x88,rotate,true);entry.anms[j].v.setUint32(0xec,0x12345678,true);}v.setUint16(0x44,state,true);v.setUint8(0x5f0,[8,16,17,16,0,8,32,255,12,64][type]);v.setFloat32(0x30,100.5+slot,true);v.setFloat32(0x34,200.25,true);v.setFloat32(0x40,0.5,true);entries.push({slot,state:hex(entry.bytes)});}
 drawBullets(pool,(vm,info)=>calls.push({...info,state:hex(vm.state)}));cases.push({entries,calls,sha256:createHash('sha256').update(pool.storage).digest('hex')});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x1403ec2a0;calls=[];digest=hashlib.sha256()
    def normalize(block,offset,encode=False):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:
                if encode:asset=n.assetByFile['etama4.anm'if struct.unpack_from('<H',block,offset+0x38)[0]>=698 else'etama3.anm'];struct.pack_into('<Q',block,p,asset+ptr)
                else:struct.pack_into('<Q',block,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
        p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
        if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        ptr=m.reg_read(UC_X86_REG_RDX);slot=(ptr-base-8)//0x620;state=bytearray(m.mem_read(ptr,288));normalize(state,0);calls.append(dict(snap=bool(m.reg_read(UC_X86_REG_R8B)),slot=slot,part='bullet',space='screen',state=state.hex()));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1400067f0,end=0x1400067f0)
    for index,c in enumerate(data['cases']):
        m.mem_write(base+8,bytes(640*0x620))
        for e in c['entries']:
            state=bytearray.fromhex(e['state'])
            for j in range(5):normalize(state,0x50+j*0x120,True)
            m.mem_write(base+8+e['slot']*0x620,bytes(state))
        m.reg_write(UC_X86_REG_RSI,base);m.reg_write(UC_X86_REG_R12D,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);calls.clear();m.emu_start(0x140011c2a,0x140011f2d,count=100000);assert calls==c['calls'],(index,'calls');actual=bytearray(m.mem_read(base+8,640*0x620))
        for e in c['entries']:
            for j in range(5):normalize(actual,e['slot']*0x620+0x50+j*0x120)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'pool');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),drawCalls=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-bullet-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
