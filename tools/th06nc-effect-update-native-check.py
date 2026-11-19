"""All effect table callbacks and continuous effect manager with actual ANM ticks.

Drifting explosions, callback-free effects, linear and radial motion are included.
Boss orbit and fade use shared supplied trig results; native CRT precision, drawing and GPU are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{EffectPool}from'./shared/th06nc/effect-pool.mjs';import{advanceEffectCallback}from'./shared/th06nc/effect-update.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const refs=[{file:'etama4.anm',archive:'th06CM.dat',base:698,slot:7},{file:'eff01.anm',archive:'th06ST.dat',base:723,slot:11}],bank=new AnmBank(),cases=[],scenes=[],hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const callback of [0,0x14002a410,0x14002a620,0x14002a830,0x14002aa50,0x14002ae30,0x14002af80])for(const current of [-1,0,1,10,60,240])for(const previous of [0,-999,1])for(const seed of [0,0xbeef,0xffff]){
 const bytes=new Uint8Array(0x198),v=new DataView(bytes.buffer),rng=new NativeRng(seed,99);for(let p=0;p<bytes.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);v.setBigUint64(0,BigInt(callback),true);v.setInt32(0x24,previous,true);v.setInt32(0x28,current,true);const before=hex(bytes),result=advanceEffectCallback({v},{rng,sin:()=>0.25,cos:()=>0.75});cases.push({callback,seed,before,after:hex(bytes),result,rng:{seed:rng.seed,count:rng.count}});
}
for(const axis of [[0,0,0],[0,0,1],[1,0,0],[0,1,0],[1,2,3],[-1,-2,-3],[1e-8,0,0],[0.001,0,1],[1,0.001,-1]])for(const strength of [0,1,30])for(const ending of [false,true])for(const fade of [0,14,15,16,127,128,254,255]){
 const bytes=new Uint8Array(0x198),v=new DataView(bytes.buffer),rng=new NativeRng(0,99);v.setBigUint64(0,BigInt(0x14002aae0),true);axis.forEach((x,i)=>v.setFloat32(0x18+i*4,x,true));v.setFloat32(0x184,strength,true);v.setFloat32(0x2c,0.5,true);v.setUint8(0x180,ending?1:0);v.setUint8(0x3c,fade);v.setUint32(0x12c,0x89abcdef,true);[100.5,200.25,-2].forEach((x,i)=>v.setFloat32(0x30+i*4,x,true));const before=hex(bytes),result=advanceEffectCallback({v},{rng,sin:()=>0.25,cos:()=>0.75});cases.push({callback:0x14002aae0,seed:0,before,after:hex(bytes),result,rng:{seed:rng.seed,count:rng.count}});
}
for(const type of [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]){
 const rng=new NativeRng(0xbeef,99),pool=new EffectPool({anmBank:bank,rng,sin:()=>0.25,cos:()=>0.75}),request={type,position:[100.5,200.25,-2],count:3,color:0x89abcdef};pool.spawn(request);const frames=[];
 for(let frame=1;frame<=120;frame++){if(type>=13&&type<=15&&frame===16)for(let i=0;i<3;i++)pool.entry(i).v.setUint8(0x180,1);pool.tick();if([1,2,3,15,30,60,120].includes(frame))frames.push({frame,activeCount:pool.activeCount,states:[0,1,2].map(i=>hex(pool.entry(i).bytes)),rng:{seed:rng.seed,count:rng.count}});}
 scenes.push({request,frames});
}console.log(JSON.stringify({refs,cases,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256();base=0x140a6ecd0
    def hook(m,a,size,u):
        if a not in [0x1402be071,0x1402be07d]:return
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    def run(addr,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(addr,n.stack+0xf000,count=1000000)
    for index,c in enumerate(data['cases']):
        m.mem_write(n.vm,bytes.fromhex(c['before']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,c['seed']))
        if c['callback']:run(c['callback'],n.vm);assert m.reg_read(UC_X86_REG_EAX)==c['result'],index
        actual=bytes(m.mem_read(n.vm,0x198));assert actual.hex()==c['after'],(index,'callback state',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,bytes.fromhex(c['after'])))if a!=b],struct.unpack_from('<3f',actual,0x174),struct.unpack_from('<3f',bytes.fromhex(c['after']),0x174));count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual)
    for sceneIndex,scene in enumerate(data['scenes']):
        m.mem_write(base,bytes(0x331a0));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(n.vm,struct.pack('<3f',*scene['request']['position']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<I',scene['request']['color']))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_EDX,scene['request']['type']),(UC_X86_REG_R8,n.vm),(UC_X86_REG_R9D,3)]:m.reg_write(reg,value)
        m.emu_start(0x14002b0d0,n.stack+0xf000,count=1000000);byFrame={f['frame']:f for f in scene['frames']};checked=set()
        for frame in range(1,121):
            if 13<=scene['request']['type']<=15 and frame==16:
                for slot in range(3):m.mem_write(base+slot*0x198+0x180,b'\1')
            run(0x14002b280,base)
            if frame not in byFrame:continue
            c=byFrame[frame];checked.add(frame);assert struct.unpack('<i',m.mem_read(base+0x33198,4))[0]==c['activeCount'],(sceneIndex,frame,'active count')
            for slot,state in enumerate(c['states']):
                actual=bytearray(m.mem_read(base+slot*0x198,0x198))
                for p in [0x130,0x138]:
                    ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                ptr=struct.unpack_from('<Q',actual,0x140)[0]
                if ptr:struct.pack_into('<Q',actual,0x140,(ptr-n.manager-0x608)//64+1)
                wanted=bytes.fromhex(state);diff=[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(sceneIndex,frame,slot,diff);digest.update(actual)
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(sceneIndex,frame,'rng')
        assert checked==set(byFrame),(sceneIndex,'unverified checkpoints')
    report=dict(scope=__doc__,callbackCases=len(data['cases']),scenes=len(data['scenes']),nativeFrames=len(data['scenes'])*120,stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/effect-pool.mjs','shared/th06nc/effect-update.mjs','shared/th06nc/effect-orbit.mjs','shared/th06nc/effect-radial.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-effect-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
