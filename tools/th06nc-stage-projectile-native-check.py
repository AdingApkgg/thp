"""First-stage combined enemy/effect/bullet/laser world, with original timeline and ANM.

All difficulty/damage variants run 5000 frames with real laser creation/update. Shared supplied trig, observed
item/UI publication services and controlled player queries exclude real player,
item entities, complete bosses/stages, background, audio and GPU equivalence.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sourceHashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/bullet-pool.mjs','shared/th06nc/bullet-pattern.mjs','shared/th06nc/bullet-motion.mjs','shared/th06nc/bullet-update.mjs','shared/th06nc/stage-world.mjs','shared/th06nc/laser-pool.mjs','shared/th06nc/laser-update.mjs','shared/th06nc/ecl-laser-control.mjs','shared/th06nc/ecl-laser-config.mjs','shared/th06nc/spell-state.mjs','shared/th06nc/spell-record.mjs','shared/th06nc/spell-bonus.mjs','shared/th06nc/projectile-cancel.mjs','shared/th06nc/effect-pool.mjs','shared/th06nc/effect-update.mjs','shared/th06nc/effect-orbit.mjs','shared/th06nc/common-layout.mjs','shared/th06nc/sprite-layout.mjs','shared/th06nc/enemy-world.mjs','shared/th06nc/boss-state.mjs','shared/th06nc/enemy-linked-effects.mjs','shared/th06nc/enemy-pool.mjs','shared/th06nc/enemy-ordinary.mjs','shared/th06nc/enemy-phase.mjs','shared/th06nc/enemy-death.mjs','shared/th06nc/ecl-timeline.mjs','shared/th06nc/ecl-dispatch.mjs','shared/th06nc/ecl-command.mjs']}
    script="""
import{readFileSync}from'node:fs';import{cancelBossProjectiles}from'./shared/th06nc/projectile-cancel.mjs';import{createHash}from'node:crypto';import{StageWorld}from'./shared/th06nc/stage-world.mjs';import{commonProjectileAssetPlan,stageEffectAssetPlan}from'./shared/th06nc/common-layout.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';import{EnemyWorld}from'./shared/th06nc/enemy-world.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const plan=stageAssetPlan(1),refs=[...plan.enemyAnimations,...commonProjectileAssetPlan(),stageEffectAssetPlan(1)],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file))])),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl')),scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const difficulty of [0,1,2,3])for(const damage of [0,20]){
 const frameLimit=5000;
 const events=[],soundSlots=[-1,-1,-1],environment={difficulty,rank:0,stageIndex:0,character:0,shot:0,rng:new NativeRng(0xbeef,99),playerPosition:[192,400,0],playerState:2,score:0n,aimTarget:[0,-1000,0],enemyDeathCount:0,itemDropIndex:0,messageField36b0:-1},bank=new AnmBank();loadStageEnemyBank(bank,resources,1);for(const r of refs.slice(plan.enemyAnimations.length))bank.load(resources.get(r.file),r.base,{slot:r.slot});
 const emptyBullets=new Uint8Array(640*0x620),emptyLasers=new Uint8Array(64*0x298),stage=new StageWorld(program,{anmBank:bank,environment,soundSlots,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,openMessage:()=>{throw Error('unexpected message');},observeBullet:(e,s)=>events.push({kind:'shot',descriptor:hex(s)}),bodyCollision:()=>0,damageQuery:()=>({damage,critical:false}),observeEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e}),laserCollision:e=>events.push({kind:'laserCollision',...e}),cancelBossProjectiles:({bullets,lasers})=>cancelBossProjectiles({bullets,lasers,publishScore:e=>events.push({kind:'projectileScore',...e})}),cancelBullets:()=>events.push({kind:'cancel'})}),world=stage.enemies,frames=[];
 world.timeline.cursor=program.timelines[0].offset;
 for(let frame=1;frame<=frameLimit;frame++){
  events.length=0;stage.tick();
  if(frame===frameLimit||frame<4||frame%16===0||[100,101,102,116,117,132,133,148,149,164,165,228,229,340,341,1883,1884,1885,1886,1887,1888,1889,1890,1940].includes(frame))frames.push({frame,bulletDebug:frame===3328?hex(stage.bullets.storage):null,bulletSha256:createHash('sha256').update(stage.bullets.storage).digest('hex'),bulletCursor:stage.bullets.cursor,bulletActiveCount:stage.bullets.activeCount,laserSha256:createHash('sha256').update(stage.lasers.storage.subarray(0,64*0x298)).digest('hex'),spell:{counter:environment.spellCounter??0,active:Boolean(environment.spellActive),id:environment.spellId??0,bonus:environment.spellBonus??0,finished:Boolean(environment.spellFinished),backgroundClock:world.spellState.backgroundClock,backgroundFrame:world.spellState.backgroundFrame??0,backgroundActive:world.spellState.backgroundActive??false,captures:world.spellState.captures,extraCaptures:world.spellState.extraCaptures,records:[...world.spellState.records].map(([id,r])=>({id,bytes:hex(r.bytes)}))},timelineFrame:world.timeline.frame,effects:{sha256:createHash('sha256').update(stage.effects.storage).digest('hex'),activeCount:stage.effects.activeCount,cursor:stage.effects.cursor},cursor:world.timeline.cursor,activeCount:world.activeCount,previousFrame:world.previousFrame,actors:world.pool.entries.flatMap(e=>e?[{slot:e.slot,state:hex(e.enemy),bounds:e.enemyAnms.get(0x108)?.boundSprite?.extra}]:[]),events:[...events],rng:{seed:environment.rng.seed,count:environment.rng.count},score:String(environment.score),soundSlots:[...soundSlots],aimTarget:environment.aimTarget,enemyDeathCount:environment.enemyDeathCount,itemDropIndex:environment.itemDropIndex,messageClock:world.timeline.messageClock,bossState:{...world.bossState},chapter:world.chapter,bossSlots:Array.from({length:8},(_,i)=>{const e=world.bossSlots[i];return e?(e.enemy.byteOffset-world.pool.storage.byteOffset)/0x10b0:null;})});
 }
 scenes.push({difficulty,damage,frameLimit,frames});
}console.log(JSON.stringify({plan,refs,timelineOffset:program.timelines[0].offset,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;owner=0x140aa1e90;programBase=n.assets+0x100000;table=n.vm+0x8000;events=[];damage=0;digest=hashlib.sha256();effectBase=0x140a6ecd0
    program=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl').read_bytes();m.mem_write(programBase,program)
    for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(n.owner+0x36b0,struct.pack('<i',-1));m.mem_write(0x1404ff27c,bytes(4));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x1404f27b5,b'\0');m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x1404f1e84,bytes(4));m.mem_write(0x1404f1e80,bytes(2));m.mem_write(0x1404ff0e8,struct.pack('<2f',384,448))
    def hook(m,a,size,u):
        if a==0x14006aba0:
            sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(kind='laserCollision',center=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_RDX),8))),size=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_R8),8))),origin=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R9),12))),angle=struct.unpack('<f',m.mem_read(sp+0x28,4))[0],graze=bool(m.mem_read(sp+0x30,1)[0])));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x140042980:m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x14002779a:
            m.reg_write(UC_X86_REG_RBX,m.reg_read(UC_X86_REG_R14)+16);m.reg_write(UC_X86_REG_RIP,0x1400279a3);return
        elif a in [0x14000ef00,0x14000f300]:events.append(dict(kind='cancel'))
        elif a in [0x1402bdee2,0x1402bdee8]:
            dst=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);size=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([src&255])*size if a==0x1402bdee2 else bytes(m.mem_read(src,size)));m.reg_write(UC_X86_REG_RAX,dst)
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',{0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a]),'little'))
        elif a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()));return
        elif a==0x140009bd0:events.append(dict(kind='projectileScore',position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),value=m.reg_read(UC_X86_REG_R8D),color=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x14006a8c0:m.reg_write(UC_X86_REG_RAX,0)
        elif a in [0x14006a980,0x140069d00]:
            if a==0x140069d00:m.mem_write(m.reg_read(UC_X86_REG_R9),b'\0')
            m.reg_write(UC_X86_REG_RAX,0 if a==0x14006a980 else damage)
        elif a in [0x14002b0d0,0x1400426e0]:
            position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
            if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]));return
            else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))))
            m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bcf20:pass
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x1402bdee2,0x1402bdee8,0x1402be065,0x1402be071,0x1402be07d,0x14000f870,0x140009bd0,0x14006a8c0,0x14006a980,0x140069d00,0x14002b0d0,0x1400426e0,0x1402bcf20,0x14002779a,0x14000ef00,0x14000f300,0x14006aba0,0x140042980]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    def run(addr,rcx=owner):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(addr,n.stack+0xf000,count=3000000)
    for sceneIndex,scene in enumerate(data['scenes']):
        damage=scene['damage'];m.reg_write(UC_X86_REG_RBX,0x1403ec2a0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140011fee,0x140012329,count=1000000);m.mem_write(0x1403ec2a0+0xff618,bytes(4));m.mem_write(0x140506c38,b'\2');run(0x140035f50);m.mem_write(effectBase,bytes(0x331a0));m.mem_write(0x1403ec2a8,bytes(640*0x620));m.mem_write(0x1404e12b8,bytes(64*0x298));m.mem_write(0x1403ec2a0,bytes(8));m.mem_write(0x140badf60,bytes(20));m.mem_write(0x140509c18,bytes(8));m.mem_write(0x140509b60,bytes(4));m.mem_write(0x1404f1e68,bytes(8));m.mem_write(0x1404f27c8,bytes(134*0x180));m.mem_write(n.owner+0x8c2,bytes(2));m.mem_write(0x1404f1e88,bytes(2));m.mem_write(0x140a6ebd0,bytes(16));m.mem_write(0x140a6ebec,b'\0');m.mem_write(0x140a6ec1c,bytes(4));m.mem_write(owner+0x10c128,struct.pack('<Q',programBase+data['timelineOffset']));m.mem_write(0x1404f27c0,struct.pack('<i',scene['difficulty']));m.mem_write(0x140a6eb90,b'\0');m.mem_write(0x140a6ec14,b'\0');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404f2798,bytes(8));m.mem_write(0x140506ae0,struct.pack('<3f',0,-1000,0));m.mem_write(0x1404ff0d8,bytes(4));byFrame={f['frame']:f for f in scene['frames']};checkedFrames=set()
        for frame in range(1,scene['frameLimit']+1):
            events.clear();run(0x1400373b0);run(0x14002b280,effectBase);run(0x140010870,0x1403ec2a0)
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
                for i in range(8):
                    p=0xbe8+i*8;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,(ptr-effectBase)//0x198+1)
                for i in range(32):
                    p=0xf80+i*8;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,(ptr-0x1404e12b8)//0x298+1)
                wanted=bytes.fromhex(actor['state']);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(sceneIndex,frame,actor['slot'],diff,actor.get('bounds'),struct.unpack('<2f',m.mem_read(struct.unpack('<Q',m.mem_read(owner+8+actor['slot']*0x10b0+0x208,8))[0]+0x1c,8)),struct.unpack_from('<3f',actual,0xb0));digest.update(actual)
            fx=bytearray(m.mem_read(effectBase,513*0x198))
            for slot in range(513):
                for offset in [0x130,0x138]:
                    p=slot*0x198+offset;ptr=struct.unpack_from('<Q',fx,p)[0]
                    if ptr:struct.pack_into('<Q',fx,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                p=slot*0x198+0x140;ptr=struct.unpack_from('<Q',fx,p)[0]
                if ptr:struct.pack_into('<Q',fx,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(fx).hexdigest()==c['effects']['sha256'],(sceneIndex,frame,'effect pool');assert struct.unpack('<2i',m.mem_read(effectBase+0x33198,8))==(c['effects']['activeCount'],c['effects']['cursor']),(sceneIndex,frame,'effect counts');digest.update(fx)
            laser=bytearray(m.mem_read(0x1404e12b8,64*0x298))
            for slot in range(64):
                for offset in [0x20,0x140]:
                    for field in [0xf0,0xf8]:
                        p=slot*0x298+offset+field;ptr=struct.unpack_from('<Q',laser,p)[0]
                        if ptr:struct.pack_into('<Q',laser,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                    p=slot*0x298+offset+0x100;ptr=struct.unpack_from('<Q',laser,p)[0]
                    if ptr:struct.pack_into('<Q',laser,p,(ptr-n.manager-0x608)//64+1)
            bullets=bytearray(m.mem_read(0x1403ec2a8,640*0x620))
            for slot in range(640):
                for offset in [0x50+j*0x120 for j in range(5)]:
                    for field in [0xf0,0xf8]:
                        p=slot*0x620+offset+field;ptr=struct.unpack_from('<Q',bullets,p)[0]
                        if ptr:struct.pack_into('<Q',bullets,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                    p=slot*0x620+offset+0x100;ptr=struct.unpack_from('<Q',bullets,p)[0]
                    if ptr:struct.pack_into('<Q',bullets,p,(ptr-n.manager-0x608)//64+1)
            
            if hashlib.sha256(bullets).hexdigest()!=c['bulletSha256']:
                wanted=bytes.fromhex(c['bulletDebug']) if c['bulletDebug'] else b'';raise AssertionError((sceneIndex,frame,'bullet pool',[(hex(p//0x620),hex(p%0x620),a,b)for p,(a,b)in enumerate(zip(bullets,wanted))if a!=b][:40]))
            assert struct.unpack('<i',m.mem_read(0x1403ec2a0+0xff618,4))[0]==c['bulletCursor'],(sceneIndex,frame,'bullet cursor');assert struct.unpack('<i',m.mem_read(0x1403ec2a0+0xf5008,4))[0]==c['bulletActiveCount'],(sceneIndex,frame,'bullet active count');digest.update(bullets)
            assert hashlib.sha256(laser).hexdigest()==c['laserSha256'],(sceneIndex,frame,'laser pool');digest.update(laser)
            assert events==c['events'],(sceneIndex,frame,events,c['events']);assert struct.unpack('<i',m.mem_read(owner,4))[0]==c['activeCount'],(sceneIndex,frame,'active count');assert struct.unpack('<2i',m.mem_read(owner+0x10c0b8,8))==(c['previousFrame'],c['timelineFrame']),(sceneIndex,frame,'clock');assert struct.unpack('<Q',m.mem_read(owner+0x10c128,8))[0]-programBase==c['cursor'],(sceneIndex,frame,'cursor')
            assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['score'],(sceneIndex,frame,'score');assert list(struct.unpack('<3f',m.mem_read(0x140506ae0,12)))==c['aimTarget'],(sceneIndex,frame,'target');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(sceneIndex,frame,'sound');assert struct.unpack('<HH',m.mem_read(owner+4,4))==(c['enemyDeathCount'],c['itemDropIndex']),(sceneIndex,frame,'item cycle');assert struct.unpack('<i',m.mem_read(0x1404ff0d8,4))[0]==c['messageClock'],(sceneIndex,frame,'message clock')
            boss=dict(active=bool(m.mem_read(0x140a6ec14,1)[0]),lifeFraction=struct.unpack('<f',m.mem_read(0x140a6ebd4,4))[0],segmentFraction=struct.unpack('<f',m.mem_read(0x140a6ebdc,4))[0],dirty=bool(m.mem_read(0x140a6ebec,1)[0]),remainingSeconds=struct.unpack('<i',m.mem_read(0x140a6ec1c,4))[0]);
            if 'bonusPopup'in c['bossState']:boss['bonusPopup']=dict(previous=struct.unpack('<i',m.mem_read(n.owner+0x6c0,4))[0],frame=struct.unpack('<i',m.mem_read(n.owner+0x6c4,4))[0],active=bool(m.mem_read(n.owner+0x6c8,1)[0]),position=list(struct.unpack('<3f',m.mem_read(n.owner+0x6cc,12))),value=struct.unpack('<i',m.mem_read(n.owner+0x6d8,4))[0])
            assert boss==c['bossState'],(sceneIndex,frame,'boss state',boss,c['bossState']);assert struct.unpack('<i',m.mem_read(0x140a6ebd0,4))[0]==c['chapter'],(sceneIndex,frame,'chapter')
            slots=[struct.unpack('<Q',m.mem_read(owner+0x10c0e8+i*8,8))[0]for i in range(8)];assert [None if p==0 else(p-owner-8)//0x10b0 for p in slots]==c['bossSlots'],(sceneIndex,frame,'boss slots')
            spell=dict(counter=struct.unpack('<i',m.mem_read(0x140badf60,4))[0],active=bool(m.mem_read(0x140badf6c,1)[0]),id=struct.unpack('<i',m.mem_read(0x140badf68,4))[0],bonus=struct.unpack('<i',m.mem_read(0x140badf70,4))[0],finished=bool(m.mem_read(0x140aa1e8e,1)[0]),backgroundClock=struct.unpack('<i',m.mem_read(0x140509c18,4))[0],backgroundFrame=struct.unpack('<i',m.mem_read(0x140509b60,4))[0],backgroundActive=bool(m.mem_read(0x140509c1c,1)[0]),captures=struct.unpack('<i',m.mem_read(0x1404f1e68,4))[0],extraCaptures=struct.unpack('<i',m.mem_read(0x1404f1e6c,4))[0]);assert spell=={k:v for k,v in c['spell'].items()if k!='records'},(sceneIndex,frame,'spell',spell,c['spell'])
            for record in c['spell']['records']:
                actual=bytes(m.mem_read(0x1404f27c8+record['id']*0x180,0x180));assert actual.hex()==record['bytes'],(sceneIndex,frame,'spell record',record['id']);digest.update(actual)
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(sceneIndex,frame,'rng')
        assert checkedFrames==set(byFrame),(sceneIndex,'unverified checkpoints',sorted(set(byFrame)-checkedFrames))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sourceHashes.items()),'Source changed while proof was running'
    report=dict(scope=__doc__,scenes=len(data['scenes']),nativeFrames=sum(s['frameLimit']for s in data['scenes']),checkpoints=sum(len(s['frames'])for s in data['scenes']),enemyStateComparisons=sum(len(f['actors'])for s in data['scenes']for f in s['frames']),stateSha256=digest.hexdigest(),sourceSha256=sourceHashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-stage-projectile-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
