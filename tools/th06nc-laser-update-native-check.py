"""Laser update loop 11610..11938 with real ANM ticks and observed collision.

Compares complete laser state and collision queries across phases/timer/geometry
boundaries. Player collision results, drawing, GPU and complete projectiles excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{LaserPool}from'./shared/th06nc/laser-pool.mjs';import{advanceLaser}from'./shared/th06nc/laser-update.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[],scenarios=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const type of [0,1])for(const mode of [0,1,2,3])for(const frame of [-1,0,1,12,30,100])for(const delay of [0,1,30])for(const fade of [0,1,20])for(const alpha of [false,true])scenarios.push({type,mode,frame,delay,fade,alpha});
for(const head of [-10,0,10,1000])for(const tail of [-20,0,100])for(const speed of [-2,0,3])for(const maximum of [0,40,500])scenarios.push({type:0,mode:1,frame:4,delay:5,fade:20,alpha:false,head,tail,speed,maximum});
for(const config of scenarios){
 const pool=new LaserPool({anmBank:bank}),descriptor=new Uint8Array(68),d=new DataView(descriptor.buffer);d.setInt16(0xc,config.type,true);d.setUint8(0x2c,1);const laser=pool.spawn(descriptor),v=laser.v;
 v.setUint8(0x290,config.mode);v.setInt32(0xc,config.frame,true);v.setInt32(0x270,config.delay,true);v.setInt32(0x18,config.fade,true);v.setUint16(0x264,config.alpha?1:0,true);v.setInt32(0x268,20,true);v.setFloat32(4,16,true);v.setFloat32(0x14,config.head??40,true);v.setFloat32(0x10,config.tail??-10,true);v.setFloat32(0x26c,config.speed??3,true);v.setFloat32(0x288,config.maximum??50,true);v.setFloat32(0x260,0.5,true);[100.5,200.25,-2].forEach((x,i)=>v.setFloat32(0x278+i*4,x,true));
 const before=Buffer.from(laser.bytes).toString('hex'),events=[];advanceLaser(laser,{collision:e=>events.push(e)});cases.push({config,before,after:Buffer.from(laser.bytes).toString('hex'),events,bindings:[laser.main,laser.end].map(vm=>refs.find(r=>r.file===vm.resource.textureName.split('/').at(-2)+'.anm')?.file??(vm===laser.main?'etama3_2.anm':'etama3.anm'))});
}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a!=0x14006aba0:return
        sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(center=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_RDX),8))),size=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_R8),8))),origin=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R9),12))),angle=struct.unpack('<f',m.mem_read(sp+0x28,4))[0],graze=bool(m.mem_read(sp+0x30,1)[0])));m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x14006aba0,end=0x14006aba0)
    for index,c in enumerate(data['cases']):
        state=bytearray.fromhex(c['before'])
        for offset,file in zip([0x20,0x140],c['bindings']):
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,offset+p)[0]
                if ptr:struct.pack_into('<Q',state,offset+p,n.assetByFile[file]+ptr)
            ptr=struct.unpack_from('<Q',state,offset+0x100)[0]
            if ptr:struct.pack_into('<Q',state,offset+0x100,n.manager+0x608+(ptr-1)*64)
        m.mem_write(n.owner,bytes(state))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,n.owner+0x14),(UC_X86_REG_R13,0),(UC_X86_REG_R12,30),(UC_X86_REG_RSI,255)]:m.reg_write(reg,value)
        for reg,value in [(UC_X86_REG_XMM7,255),(UC_X86_REG_XMM9,1.2),(UC_X86_REG_XMM6,0.03125),(UC_X86_REG_XMM8,640),(UC_X86_REG_XMM10,1.5707963705062866),(UC_X86_REG_XMM12,0),(UC_X86_REG_XMM15,0.5)]:m.reg_write(reg,int.from_bytes(struct.pack('<f',value),'little'))
        events.clear();m.emu_start(0x140011610,0x14001172f,count=100000);actual=bytearray(m.mem_read(n.owner,0x298))
        for offset,file in zip([0x20,0x140],c['bindings']):
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,offset+p)[0]
                if ptr:struct.pack_into('<Q',actual,offset+p,ptr-n.assetByFile[file])
            ptr=struct.unpack_from('<Q',actual,offset+0x100)[0]
            if ptr:struct.pack_into('<Q',actual,offset+0x100,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,c['config'],diff);assert events==c['events'],(index,c['config'],'collision',events,c['events']);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/laser-update.mjs','shared/th06nc/laser-pool.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-laser-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
