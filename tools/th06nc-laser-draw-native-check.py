"""Laser draw manager: beam/end-cap placement, color, scales and draw order.

Original owner draw block executes with observed ANM draw APIs and shared trig
results. Lower draw helpers, projection, GPU pixels and full frames excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{LaserPool}from'./shared/th06nc/laser-pool.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[],hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const tail of [-10,0,16,31.999,32,33,640])for(const speed of [-1,0,1])for(const width of [0,4,10,20])for(const active of [false,true]){
 const pool=new LaserPool({anmBank:bank}),descriptor=new Uint8Array(68),d=new DataView(descriptor.buffer);d.setUint8(0x2c,1);pool.spawn(descriptor);pool.spawn(descriptor);for(let i=2;i<63;i++)pool.entry(i).v.setUint8(0x274,1);pool.spawn(descriptor);for(let i=2;i<63;i++)pool.entry(i).v.setUint8(0x274,0);
 for(const slot of [0,1,63]){const v=pool.entry(slot).v;v.setUint8(0x274,active?1:0);v.setFloat32(0x10,tail,true);v.setFloat32(0x14,tail+100,true);v.setFloat32(0x260,0.5,true);v.setFloat32(0x26c,speed,true);v.setFloat32(4,width,true);v.setFloat32(0x278,100.5+slot,true);v.setFloat32(0x27c,200.25,true);v.setUint32(0x10c,0x89abcdef,true);}
 const before=hex(pool.storage),calls=[];pool.draw((vm,info)=>calls.push({...info,state:hex(vm.state)}),{sin:()=>0.25,cos:()=>0.75});cases.push({before,calls,sha256:createHash('sha256').update(pool.storage).digest('hex')});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;poolBase=0x1404e12b8;calls=[];digest=hashlib.sha256()
    def normalize(state,offset,file,encode=False):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,n.assetByFile[file]+ptr if encode else ptr-n.assetByFile[file])
        p=offset+0x100;ptr=struct.unpack_from('<Q',state,p)[0]
        if ptr:struct.pack_into('<Q',state,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a in [0x140004dc0,0x1400067f0]:
            ptr=m.reg_read(UC_X86_REG_RDX);slot=(ptr-poolBase)//0x298;offset=(ptr-poolBase)%0x298;part='beam'if offset==0x20 else'origin';state=bytearray(m.mem_read(ptr,288));normalize(state,0,'etama3_2.anm'if part=='beam'else'etama3.anm');calls.append(dict(snap=False if part=='beam'else bool(m.reg_read(UC_X86_REG_R8B)),slot=slot,part=part,space='world'if part=='beam'else'screen',state=state.hex()));m.reg_write(UC_X86_REG_RAX,0)
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x140004dc0,0x1400067f0,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    for index,c in enumerate(data['cases']):
        before=bytearray.fromhex(c['before'])
        for slot in range(65):
            for offset,file in [(0x20,'etama3_2.anm'),(0x140,'etama3.anm')]:normalize(before,slot*0x298+offset,file,True)
        m.mem_write(poolBase,bytes(before));m.reg_write(UC_X86_REG_RSI,0x1403ec2a0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_XMM7,0);m.reg_write(UC_X86_REG_XMM10,int.from_bytes(struct.pack('<f',0.5),'little'));calls.clear();m.emu_start(0x1400119a7,0x140011b0a,count=100000);assert calls==c['calls'],(index,'calls');actual=bytearray(m.mem_read(poolBase,65*0x298))
        for slot in range(65):
            for offset,file in [(0x20,'etama3_2.anm'),(0x140,'etama3.anm')]:normalize(actual,slot*0x298+offset,file)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'pool');digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),drawCalls=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/laser-draw.mjs','shared/th06nc/laser-pool.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-laser-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
