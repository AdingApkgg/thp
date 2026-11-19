"""Custom 2 continuous interleaved owners with real ordinary bullet allocation.

Shared snapshots/angles persist across both owners, whose moving positions and
start times differ. Compare complete enemy and 640-bullet pool, cursor, RNG,
sound and ordered requests at every call. Three shot modes and pool exhaustion
are included. No motion/draw/host-scene or complete-game claim.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom-stage3.mjs','shared/th06nc/ecl-custom.mjs','shared/th06nc/bullet-pool.mjs','shared/th06nc/bullet-pattern.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{executeEclCustomCallback}from'./shared/th06nc/ecl-custom.mjs';import{createStageThreePatternState}from'./shared/th06nc/ecl-custom-stage3.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),scenes=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const mode of [0,3,8])for(const occupied of [0,639,640])for(const seed of [0,0xbeef]){
 const rng=new NativeRng(seed,99),environment={rng,playerPosition:[192,400,0],stageThreePatternState:createStageThreePatternState()},soundSlots=[-1,22,-1],pool=new BulletPool({anmBank:bank,environment}),owners=[0,1].map(index=>{const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);v.setBigUint64(0x98,0x140032cf0n,true);v.setInt32(0x54,index?60:90,true);v.setFloat32(0x64,60+index*20,true);const d=new DataView(enemy.buffer,0x26c,108);d.setFloat32(4,3.7,true);d.setFloat32(8,.4,true);d.setInt16(0x18,3,true);d.setInt16(0x1a,2,true);d.setInt16(0x2c,3,true);d.setInt16(0x2e,1,true);d.setInt16(0x30,mode,true);d.setFloat32(0x38,.6,true);return enemy;});for(let i=0;i<occupied;i++)pool.entry(i).v.setUint16(0x44,1,true);pool.cursor=639;const initial=owners.map(hex),calls=[];
 for(let frame=0;frame<=90;frame++){environment.playerPosition=[Math.fround(192+frame*.25),Math.fround(400-frame*.1),0];for(let index=0;index<2;index++){const enemy=owners[index],v=new DataView(enemy.buffer);if(frame<index*10||!v.getBigUint64(0x98,true))continue;const position=[Math.fround(100.5+index*100+frame*.1),Math.fround(200.25+frame*.125),-2];position.forEach((n,i)=>v.setFloat32(0xb0+i*4,n,true));const events=[];executeEclCustomCallback(enemy,{environment,soundSlots,fireBullets:(e,d)=>{events.push(hex(d));return pool.spawn(d);}});calls.push({frame,index,position,player:environment.playerPosition,enemy:hex(enemy),positions:hex(environment.stageThreePatternState.positions),angles:hex(environment.stageThreePatternState.angles),events,cursor:pool.cursor,poolSha:sha(pool.storage),soundSlots:[...soundSlots],rng:{seed:rng.seed,count:rng.count}});}}
 scenes.push({mode,occupied,seed,initial,calls});
}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x1403ec2a0;poolBase=base+8;events=[];digest=hashlib.sha256();checks=0
    m.reg_write(UC_X86_REG_RBX,base);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140011fee,0x140012329,count=1000000);m.mem_write(0x1404f27b5,b'\0')
    def hook(m,a,size,u):
        if a==0x14000f870:events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex());return
        x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];y=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM1).to_bytes(16,'little')[:4])[0];value=math.atan2(x,y)if a==0x1402be065 else math.cos(x)if a==0x1402be071 else math.sin(x);m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000f870,0x1402be065,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for si,scene in enumerate(data['scenes']):
        pool=bytearray(640*0x620)
        for slot in range(scene['occupied']):struct.pack_into('<H',pool,slot*0x620+0x44,1)
        m.mem_write(poolBase,bytes(pool));m.mem_write(base+0xff618,struct.pack('<i',639));m.mem_write(0x140a6ec40,struct.pack('<IH',99,scene['seed']));m.mem_write(0x140509670,struct.pack('<3i',-1,22,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x140aa1e70,bytes(28));m.mem_write(0x140a6eba0,bytes(24))
        for index,enemy in enumerate(scene['initial']):m.mem_write(n.owner+index*0x2000,bytes.fromhex(enemy))
        for c in scene['calls']:
            owner=n.owner+c['index']*0x2000;m.mem_write(owner+0xb0,struct.pack('<3f',*c['position']));m.mem_write(0x140506ad0,struct.pack('<3f',*c['player']));events.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(0x140032cf0,n.stack+0xf000,count=30000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(si,c['frame'],'instruction limit');actual=bytes(m.mem_read(owner,0x10b0));assert actual.hex()==c['enemy'],(si,c['frame'],c['index'],'enemy');assert events==c['events'],(si,c['frame'],'requests');assert bytes(m.mem_read(0x140aa1e70,28)).hex()==c['positions'],(si,c['frame'],'positions');assert bytes(m.mem_read(0x140a6eba0,24)).hex()==c['angles'],(si,c['frame'],'angles')
            block=bytearray(m.mem_read(poolBase,640*0x620))
            for slot in range(640):
                for j in range(5):
                    offset=slot*0x620+0x50+j*0x120
                    for field in [0xf0,0xf8]:
                        p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
                        if ptr:struct.pack_into('<Q',block,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                    p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
                    if ptr:struct.pack_into('<Q',block,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(block).hexdigest()==c['poolSha'],(si,c['frame'],'pool');assert struct.unpack('<i',m.mem_read(base+0xff618,4))[0]==c['cursor'],(si,c['frame'],'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(si,c['frame'],'RNG');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(si,c['frame'],'sound');digest.update(block);digest.update(actual);checks+=1
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,scenes=len(data['scenes']),calls=checks,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-stage3-pattern-pools-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
