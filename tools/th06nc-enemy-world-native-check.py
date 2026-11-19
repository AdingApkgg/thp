"""First-stage world through boss registration: timeline, spawning, ECL and ANM.

Actual first 1940 stage frames run continuously. Shared supplied trig, observed
bullet/effect/item services and controlled player queries exclude real player,
projectiles, item/effect entities, boss attacks/death, background, audio and GPU equivalence.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sourceHashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/enemy-world.mjs','shared/th06nc/boss-state.mjs','shared/th06nc/enemy-linked-effects.mjs','shared/th06nc/enemy-pool.mjs','shared/th06nc/enemy-ordinary.mjs','shared/th06nc/enemy-phase.mjs','shared/th06nc/enemy-death.mjs','shared/th06nc/ecl-timeline.mjs','shared/th06nc/ecl-dispatch.mjs','shared/th06nc/ecl-command.mjs']}
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';import{EnemyWorld}from'./shared/th06nc/enemy-world.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const frameLimit=1940,plan=stageAssetPlan(1),resources=new Map(plan.enemyAnimations.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+r.file))])),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl')),scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const difficulty of [0,1,2,3])for(const damage of [0,20]){
 const events=[],soundSlots=[-1,-1,-1],environment={difficulty,rank:0,stageIndex:0,character:0,shot:0,rng:new NativeRng(0xbeef,99),playerPosition:[192,400,0],score:0n,aimTarget:[0,-1000,0],enemyDeathCount:0,itemDropIndex:0,messageField36b0:-1},bank=new AnmBank();loadStageEnemyBank(bank,resources,1);
 const world=new EnemyWorld(program,{anmBank:bank,environment,soundSlots,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,openMessage:()=>{throw Error('unexpected message');},fireBullets:(e,s)=>events.push({kind:'shot',descriptor:hex(s)}),bodyCollision:()=>0,damageQuery:()=>({damage,critical:false}),spawnEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e}),cancelBullets:()=>events.push({kind:'cancel'})}),frames=[];
 world.timeline.cursor=program.timelines[0].offset;
 for(let frame=1;frame<=frameLimit;frame++){
  events.length=0;world.tick();
  if(frame<4||frame%16===0||[100,101,102,116,117,132,133,148,149,164,165,228,229,340,341,1883,1884,1885,1886,1887,1888,1889,1890,1940].includes(frame))frames.push({frame,cursor:world.timeline.cursor,activeCount:world.activeCount,previousFrame:world.previousFrame,actors:world.pool.entries.flatMap(e=>e?[{slot:e.slot,state:hex(e.enemy),bounds:e.enemyAnms.get(0x108)?.boundSprite?.extra}]:[]),events:[...events],rng:{seed:environment.rng.seed,count:environment.rng.count},score:String(environment.score),soundSlots:[...soundSlots],aimTarget:environment.aimTarget,enemyDeathCount:environment.enemyDeathCount,itemDropIndex:environment.itemDropIndex,messageClock:world.timeline.messageClock,bossState:{...world.bossState},chapter:world.chapter,bossSlots:Array.from({length:8},(_,i)=>{const e=world.bossSlots[i];return e?(e.enemy.byteOffset-world.pool.storage.byteOffset)/0x10b0:null;})});
 }
 scenes.push({difficulty,damage,frames});
}console.log(JSON.stringify({frameLimit,plan,timelineOffset:program.timelines[0].offset,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['plan']['enemyAnimations']);m=n.m;owner=0x140aa1e90;programBase=n.assets+0x100000;table=n.vm+0x8000;events=[];damage=0;digest=hashlib.sha256()
    program=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl').read_bytes();m.mem_write(programBase,program)
    for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(n.owner+0x36b0,struct.pack('<i',-1));m.mem_write(0x1404ff27c,bytes(4));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x1404f27b5,b'\0');m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x1404f1e84,bytes(4));m.mem_write(0x1404f1e80,bytes(2));m.mem_write(0x1404ff0e8,struct.pack('<2f',384,448))
    def hook(m,a,size,u):
        if a in [0x1402bdee2,0x1402bdee8]:
            dst=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);size=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([src&255])*size if a==0x1402bdee2 else bytes(m.mem_read(src,size)));m.reg_write(UC_X86_REG_RAX,dst)
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',{0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a]),'little'))
        elif a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()));m.reg_write(UC_X86_REG_RAX,0)
        elif a in [0x14006a980,0x140069d00]:
            if a==0x140069d00:m.mem_write(m.reg_read(UC_X86_REG_R9),b'\0')
            m.reg_write(UC_X86_REG_RAX,0 if a==0x14006a980 else damage)
        elif a in [0x14002b0d0,0x1400426e0]:
            position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
            if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]))
            else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))))
            m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bcf20:pass
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x1402bdee2,0x1402bdee8,0x1402be065,0x1402be071,0x1402be07d,0x14000f870,0x14006a980,0x140069d00,0x14002b0d0,0x1400426e0,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    def run(addr):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(addr,n.stack+0xf000,count=3000000)
    for sceneIndex,scene in enumerate(data['scenes']):
        damage=scene['damage'];run(0x140035f50);m.mem_write(0x140a6ebd0,bytes(16));m.mem_write(0x140a6ebec,b'\0');m.mem_write(0x140a6ec1c,bytes(4));m.mem_write(owner+0x10c128,struct.pack('<Q',programBase+data['timelineOffset']));m.mem_write(0x1404f27c0,struct.pack('<i',scene['difficulty']));m.mem_write(0x140a6eb90,b'\0');m.mem_write(0x140a6ec14,b'\0');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404f2798,bytes(8));m.mem_write(0x140506ae0,struct.pack('<3f',0,-1000,0));m.mem_write(0x1404ff0d8,bytes(4));byFrame={f['frame']:f for f in scene['frames']};checkedFrames=set()
        for frame in range(1,data['frameLimit']+1):
            events.clear();run(0x1400373b0)
            if frame not in byFrame:continue
            c=byFrame[frame];checkedFrames.add(frame)
            for actor in c['actors']:
                actual=bytearray(m.mem_read(owner+8+actor['slot']*0x10b0,0x10b0))
                for p in [0x88,*[0xcb0+i*96 for i in range(8)]]:
                    ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-programBase)
                for offset in [0x108,*[0x2d8+i*288 for i in range(8)]]:
                    for p in [0xf0,0xf8]:
                        ptr=struct.unpack_from('<Q',actual,offset+p)[0]
                        if ptr:
                            base=next(lo for lo,hi in n.ranges if lo<=ptr<hi);struct.pack_into('<Q',actual,offset+p,ptr-base)
                    ptr=struct.unpack_from('<Q',actual,offset+0x100)[0]
                    if ptr:struct.pack_into('<Q',actual,offset+0x100,(ptr-n.manager-0x608)//64+1)
                wanted=bytes.fromhex(actor['state']);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(sceneIndex,frame,actor['slot'],diff,actor.get('bounds'),struct.unpack('<2f',m.mem_read(struct.unpack('<Q',m.mem_read(owner+8+actor['slot']*0x10b0+0x208,8))[0]+0x1c,8)),struct.unpack_from('<3f',actual,0xb0));digest.update(actual)
            assert events==c['events'],(sceneIndex,frame,events,c['events']);assert struct.unpack('<i',m.mem_read(owner,4))[0]==c['activeCount'],(sceneIndex,frame,'active count');assert struct.unpack('<2i',m.mem_read(owner+0x10c0b8,8))==(c['previousFrame'],frame),(sceneIndex,frame,'clock');assert struct.unpack('<Q',m.mem_read(owner+0x10c128,8))[0]-programBase==c['cursor'],(sceneIndex,frame,'cursor')
            assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['score'],(sceneIndex,frame,'score');assert list(struct.unpack('<3f',m.mem_read(0x140506ae0,12)))==c['aimTarget'],(sceneIndex,frame,'target');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(sceneIndex,frame,'sound');assert struct.unpack('<HH',m.mem_read(owner+4,4))==(c['enemyDeathCount'],c['itemDropIndex']),(sceneIndex,frame,'item cycle');assert struct.unpack('<i',m.mem_read(0x1404ff0d8,4))[0]==c['messageClock'],(sceneIndex,frame,'message clock')
            boss=dict(active=bool(m.mem_read(0x140a6ec14,1)[0]),lifeFraction=struct.unpack('<f',m.mem_read(0x140a6ebd4,4))[0],segmentFraction=struct.unpack('<f',m.mem_read(0x140a6ebdc,4))[0],dirty=bool(m.mem_read(0x140a6ebec,1)[0]),remainingSeconds=struct.unpack('<i',m.mem_read(0x140a6ec1c,4))[0]);assert boss==c['bossState'],(sceneIndex,frame,'boss state',boss,c['bossState']);assert struct.unpack('<i',m.mem_read(0x140a6ebd0,4))[0]==c['chapter'],(sceneIndex,frame,'chapter')
            slots=[struct.unpack('<Q',m.mem_read(owner+0x10c0e8+i*8,8))[0]for i in range(8)];assert [None if p==0 else(p-owner-8)//0x10b0 for p in slots]==c['bossSlots'],(sceneIndex,frame,'boss slots')
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(sceneIndex,frame,'rng')
        assert checkedFrames==set(byFrame),(sceneIndex,'unverified checkpoints',sorted(set(byFrame)-checkedFrames))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sourceHashes.items()),'Source changed while proof was running'
    report=dict(scope=__doc__,scenes=len(data['scenes']),nativeFrames=len(data['scenes'])*data['frameLimit'],checkpoints=sum(len(s['frames'])for s in data['scenes']),enemyStateComparisons=sum(len(f['actors'])for s in data['scenes']for f in s['frames']),stateSha256=digest.hexdigest(),sourceSha256=sourceHashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-world-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
