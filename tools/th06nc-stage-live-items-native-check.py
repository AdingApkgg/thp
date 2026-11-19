"""First-stage live combat including real item entities and pickups, shots, damage, contact, timeline and ANM.

Four profiles on Normal run 5000 frames with continuous movement/fire and actual damage/contact. Shared supplied trig, observed
EF00/F300 conversion and UI publication services exclude bombs, complete bosses/stages,
message/render workflows, background, audio and GPU equivalence. C++ item TLS init bypassed.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sourceHashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/item-pool.mjs','shared/th06nc/item-motion.mjs','shared/th06nc/item-collect.mjs','shared/th06nc/score-popup-pool.mjs','shared/th06nc/player-init.mjs','shared/th06nc/player-state.mjs','shared/th06nc/player-update.mjs','shared/th06nc/player-input.mjs','shared/th06nc/player-motion.mjs','shared/th06nc/player-movement.mjs','shared/th06nc/player-options.mjs','shared/th06nc/player-life.mjs','shared/th06nc/player-shot-programs.mjs','shared/th06nc/player-shot-build.mjs','shared/th06nc/player-fire.mjs','shared/th06nc/player-shot-update.mjs','shared/th06nc/player-damage.mjs','shared/th06nc/player-bullet-contact.mjs','shared/th06nc/player-laser-contact.mjs','shared/th06nc/bullet-pool.mjs','shared/th06nc/bullet-pattern.mjs','shared/th06nc/bullet-motion.mjs','shared/th06nc/bullet-update.mjs','shared/th06nc/stage-world.mjs','shared/th06nc/laser-pool.mjs','shared/th06nc/laser-update.mjs','shared/th06nc/ecl-laser-control.mjs','shared/th06nc/ecl-laser-config.mjs','shared/th06nc/spell-state.mjs','shared/th06nc/spell-record.mjs','shared/th06nc/spell-bonus.mjs','shared/th06nc/projectile-cancel.mjs','shared/th06nc/effect-pool.mjs','shared/th06nc/effect-update.mjs','shared/th06nc/effect-orbit.mjs','shared/th06nc/common-layout.mjs','shared/th06nc/sprite-layout.mjs','shared/th06nc/enemy-world.mjs','shared/th06nc/boss-state.mjs','shared/th06nc/enemy-linked-effects.mjs','shared/th06nc/enemy-pool.mjs','shared/th06nc/enemy-ordinary.mjs','shared/th06nc/enemy-phase.mjs','shared/th06nc/enemy-death.mjs','shared/th06nc/ecl-timeline.mjs','shared/th06nc/ecl-dispatch.mjs','shared/th06nc/ecl-command.mjs']}
    script="""
import{readFileSync}from'node:fs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{cancelBossProjectiles}from'./shared/th06nc/projectile-cancel.mjs';import{createHash}from'node:crypto';import{StageWorld}from'./shared/th06nc/stage-world.mjs';import{commonProjectileAssetPlan,stageEffectAssetPlan}from'./shared/th06nc/common-layout.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';import{EnemyWorld}from'./shared/th06nc/enemy-world.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const plan=stageAssetPlan(1),refs=[...plan.enemyAnimations,...commonProjectileAssetPlan(),stageEffectAssetPlan(1)],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file))])),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl')),scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const difficulty of [1])for(const character of [0,1])for(const shot of [0,1]){
 const frameLimit=5000,damage=0,position=[192,384,Math.fround(0.49)];
 const events=[],soundSlots=[-1,-1,-1],environment={atan2:Math.atan2,stageGraze:0,totalGraze:0,inputFlags:0,grazeCountersDisabled:false,difficulty,rank:0,stageIndex:0,character,shot,playerPower:128,lives:9,bombs:3,defaultBombs:3,deathCount:0,powerItemChain:1,continueState:0,gameOverRequested:false,lifeProtection:false,replay:false,rng:new NativeRng(0xbeef,99),playerPosition:position,score:0n,aimTarget:[0,-1000,0],enemyDeathCount:0,itemDropIndex:0,messageField36b0:-1},bank=new AnmBank();loadStageEnemyBank(bank,resources,1);for(const r of refs.slice(plan.enemyAnimations.length))bank.load(resources.get(r.file),r.base,{slot:r.slot});const playerRef=playerAssetPlan(character);bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+playerRef.archive+'/'+playerRef.file)),playerRef.base,{slot:playerRef.slot});const player=new PlayerState({anmBank:bank,environment});
 const emptyBullets=new Uint8Array(640*0x620),emptyLasers=new Uint8Array(64*0x298),stage=new StageWorld(program,{anmBank:bank,environment,player,playerBounds:[0,0,384,448],soundSlots,sin:Math.sin,cos:Math.cos,atan2:Math.atan2,openMessage:()=>{throw Error('unexpected message');},observeBullet:(e,s)=>events.push({kind:'shot',descriptor:hex(s)}),observeEffect:e=>events.push({kind:'effect',...e}),observeItem:e=>events.push({kind:'item',...e}),observePointItem:e=>events.push({kind:'point',...e}),observeLaserCollision:e=>events.push({kind:'laserCollision',...e}),cancelBossProjectiles:({bullets,lasers})=>cancelBossProjectiles({bullets,lasers,publishScore:e=>events.push({kind:'projectileScore',...e})}),cancelBullets:()=>events.push({kind:'cancel'})}),world=stage.enemies,frames=[];
 world.timeline.cursor=program.timelines[0].offset;
 for(let frame=1;frame<=frameLimit;frame++){
  events.length=0;const input=1|(frame%240<120?0x40:0x80)|(frame%120<60?4:0);stage.tick(input);
  if(frame===frameLimit||frame<4||(frame>=2680&&frame<=2730)||frame%16===0||[100,101,102,116,117,132,133,148,149,164,165,228,229,340,341,1883,1884,1885,1886,1887,1888,1889,1890,1940].includes(frame))frames.push({frame,player:{position:player.position,hitRadius:player.hitRadius,state:player.state,deathBombFrames:player.deathBombFrames,hitTimer:player.hitTimer,hitAnimationTimers:player.hitAnimationTimers},items:{sha256:createHash('sha256').update(stage.items.storage).digest('hex'),activeCount:stage.items.activeCount,cursor:stage.items.cursor,popups:createHash('sha256').update(stage.popups.storage).digest('hex'),popupCursor:stage.popups.cursor,smallCursor:stage.popups.smallCursor},playerSha256:createHash('sha256').update(player.bytes).digest('hex'),playerDebug:frame<4||(frame>=2680&&frame<=2730)||frame%128===0?hex(player.bytes):null,life:{power:environment.playerPower,lives:environment.lives,bombs:environment.bombs,deaths:environment.deathCount},grazeCounters:[environment.stageGraze,environment.totalGraze],inputFlags:environment.inputFlags,bulletDebug:frame===3328?hex(stage.bullets.storage):null,bulletSha256:createHash('sha256').update(stage.bullets.storage).digest('hex'),bulletCursor:stage.bullets.cursor,bulletActiveCount:stage.bullets.activeCount,laserSha256:createHash('sha256').update(stage.lasers.storage.subarray(0,64*0x298)).digest('hex'),spell:{counter:environment.spellCounter??0,active:Boolean(environment.spellActive),id:environment.spellId??0,bonus:environment.spellBonus??0,finished:Boolean(environment.spellFinished),backgroundClock:world.spellState.backgroundClock,backgroundFrame:world.spellState.backgroundFrame??0,backgroundActive:world.spellState.backgroundActive??false,captures:world.spellState.captures,extraCaptures:world.spellState.extraCaptures,records:[...world.spellState.records].map(([id,r])=>({id,bytes:hex(r.bytes)}))},timelineFrame:world.timeline.frame,effects:{debug:character===0&&shot===0&&frame>=2680&&frame<=2730?hex(stage.effects.storage):null,sha256:createHash('sha256').update(stage.effects.storage).digest('hex'),activeCount:stage.effects.activeCount,cursor:stage.effects.cursor},cursor:world.timeline.cursor,activeCount:world.activeCount,previousFrame:world.previousFrame,actors:world.pool.entries.flatMap(e=>e?[{slot:e.slot,state:hex(e.enemy),bounds:e.enemyAnms.get(0x108)?.boundSprite?.extra}]:[]),events:[...events],rng:{seed:environment.rng.seed,count:environment.rng.count},score:String(environment.score),soundSlots:[...soundSlots],aimTarget:environment.aimTarget,enemyDeathCount:environment.enemyDeathCount,itemDropIndex:environment.itemDropIndex,messageClock:world.timeline.messageClock,bossState:{...world.bossState},chapter:world.chapter,bossSlots:Array.from({length:8},(_,i)=>{const e=world.bossSlots[i];return e?(e.enemy.byteOffset-world.pool.storage.byteOffset)/0x10b0:null;})});
 }
 scenes.push({difficulty,damage,position,character,shot,playerRef,frameLimit,frames});
}console.log(JSON.stringify({plan,refs,timelineOffset:program.timelines[0].offset,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;owner=0x140aa1e90;programBase=n.assets+0x100000;table=n.vm+0x8000;events=[];damage=0;digest=hashlib.sha256();effectBase=0x140a6ecd0
    program=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl').read_bytes();m.mem_write(programBase,program)
    for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(n.owner+0x36b0,struct.pack('<i',-1));m.mem_write(0x1404ff27c,bytes(4));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x1404f27b5,b'\0');m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x1404f1e84,bytes(4));m.mem_write(0x1404f1e80,bytes(2));m.mem_write(0x1404ff0e8,struct.pack('<2f',384,448))
    def hook(m,a,size,u):
        if a==0x140027fbb:
            sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(kind='point',position=list(struct.unpack('<3f',m.mem_read(sp+0x58,12)))));return
        if a==0x14006aba0:
            sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(kind='laserCollision',center=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_RDX),8))),size=list(struct.unpack('<2f',m.mem_read(m.reg_read(UC_X86_REG_R8),8))),origin=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R9),12))),angle=struct.unpack('<f',m.mem_read(sp+0x28,4))[0],graze=bool(m.mem_read(sp+0x30,1)[0])));return
        elif a==0x1400429c2:
            m.reg_write(UC_X86_REG_RAX,n.vm+0xf000);m.reg_write(UC_X86_REG_RIP,0x1400429cb);return
        elif a==0x14002779a:
            m.reg_write(UC_X86_REG_RBX,m.reg_read(UC_X86_REG_R14)+16);m.reg_write(UC_X86_REG_RIP,0x1400279a3);return
        elif a in [0x14000ef00,0x14000f300]:events.append(dict(kind='cancel'))
        elif a in [0x1402bdee2,0x1402bdee8]:
            dst=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);size=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([src&255])*size if a==0x1402bdee2 else bytes(m.mem_read(src,size)));m.reg_write(UC_X86_REG_RAX,dst)
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];y=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM1).to_bytes(16,'little')[:4])[0];value=math.atan2(x,y)if a==0x1402be065 else math.cos(x)if a==0x1402be071 else math.sin(x);m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'))
        elif a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()));return
        elif a==0x140009bd0:
            ret=struct.unpack('<Q',m.mem_read(m.reg_read(UC_X86_REG_RSP),8))[0]
            if 0x140042d00<=ret<0x140043796:return
            events.append(dict(kind='projectileScore',position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),value=m.reg_read(UC_X86_REG_R8D),color=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x14006a8c0:m.reg_write(UC_X86_REG_RAX,0)
        elif a in [0x14006a980,0x140069d00]:return
        elif a in [0x14002b0d0,0x1400426e0]:
            position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
            if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]));return
            else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))));return
            m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bcf20:pass
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x1402bdee2,0x1402bdee8,0x1402be065,0x1402be071,0x1402be07d,0x14000f870,0x140009bd0,0x14006a8c0,0x14006a980,0x140069d00,0x14002b0d0,0x1400426e0,0x1402bcf20,0x14002779a,0x140027fbb,0x14000ef00,0x14000f300,0x14006aba0,0x1400429c2]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    def run(addr,rcx=owner):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(addr,n.stack+0xf000,count=3000000)
    for sceneIndex,scene in enumerate(data['scenes']):
        n.load_title([*data['refs'],scene['playerRef']]);m.mem_write(0x1404ff3a0,bytes(0xa2b8));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));damage=scene['damage'];m.mem_write(0x140baf0d0,bytes(1025*0x160+12));m.mem_write(0x140c07238,bytes(4));m.mem_write(0x1403de870,bytes(515*40));m.mem_write(0x1403de628,bytes(8));m.mem_write(n.vm+0xf000,struct.pack('<Q',n.vm+0xf100));m.mem_write(n.vm+0xf104,struct.pack('<i',0x7fffffff));m.mem_write(0x140c25510,struct.pack('<3f',16,16,16));m.mem_write(0x1404f27ba,bytes(4));m.reg_write(UC_X86_REG_RBX,0x1403ec2a0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140011fee,0x140012329,count=1000000);m.mem_write(0x1403ec2a0+0xff618,bytes(4));m.mem_write(0x140506aec,struct.pack('<f',3));m.mem_write(0x140506c38,b'\0');m.mem_write(0x140506adc,bytes(4));m.mem_write(0x140506bf4,bytes(8));m.mem_write(0x140506d88,bytes(16));m.mem_write(0x1404ff0cc,bytes(8));m.mem_write(0x140a6ec18,bytes(4));m.mem_write(0x140509268,b'\0');run(0x140035f50);m.mem_write(effectBase,bytes(0x331a0));m.mem_write(0x1403ec2a8,bytes(640*0x620));m.mem_write(0x1404e12b8,bytes(64*0x298));m.mem_write(0x1403ec2a0,bytes(8));m.mem_write(0x140badf60,bytes(20));m.mem_write(0x140509c18,bytes(8));m.mem_write(0x140509b60,bytes(4));m.mem_write(0x1404f1e68,bytes(8));m.mem_write(0x1404f27c8,bytes(134*0x180));m.mem_write(n.owner+0x8c2,bytes(2));m.mem_write(0x1404f1e88,bytes(2));m.mem_write(0x140a6ebd0,bytes(16));m.mem_write(0x140a6ebec,b'\0');m.mem_write(0x140a6ec1c,bytes(4));m.mem_write(owner+0x10c128,struct.pack('<Q',programBase+data['timelineOffset']));m.mem_write(0x1404f27c0,struct.pack('<i',scene['difficulty']));m.mem_write(0x140a6eb90,b'\0');m.mem_write(0x140a6ec14,b'\0');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404f2798,bytes(8));m.mem_write(0x140506ae0,struct.pack('<3f',0,-1000,0));m.mem_write(0x1404ff0d8,bytes(4));byFrame={f['frame']:f for f in scene['frames']};checkedFrames=set();m.mem_write(0x1404f1e88,struct.pack('<H',128));m.mem_write(0x1404ff0f0,bytes([9,3,0]));m.mem_write(0x1404f1e60,bytes(4));m.mem_write(0x1404ff0dd,b'\1');m.mem_write(0x1404f27c4,b'\0');m.mem_write(0x1404f27b1,b'\0');m.mem_write(0x1404f27b4,b'\0');m.mem_write(0x1404ff0e0,struct.pack('<4f',0,0,384,448));m.mem_write(0x140c21de1,b'\3');m.mem_write(0x140c21d9c,struct.pack('<i',3));run(0x140068160,0x1404ff3a0);previousInput=0
        for frame in range(1,scene['frameLimit']+1):
            events.clear();current=1|(0x40 if frame%240<120 else 0x80)|(4 if frame%120<60 else 0);m.mem_write(0x140a6ec60,struct.pack('<2I',current,previousInput));previousInput=current;run(0x140068820,0x1404ff3a0);run(0x1400373b0);run(0x14002b280,effectBase);run(0x140010870,0x1403ec2a0)
            if frame not in byFrame:continue
            c=byFrame[frame];checkedFrames.add(frame)
            item=bytearray(m.mem_read(0x140baf0d8,1025*0x160))
            for slot in range(1025):
                offset=slot*0x160+0x38
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',item,p)[0]
                    if ptr:struct.pack_into('<Q',item,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                p=offset+0x100;ptr=struct.unpack_from('<Q',item,p)[0]
                if ptr:struct.pack_into('<Q',item,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(item).hexdigest()==c['items']['sha256'],(sceneIndex,frame,'item pool')
            assert struct.unpack('<i',m.mem_read(0x140baf0d0,4))[0]==c['items']['activeCount'],(sceneIndex,frame,'item count')
            assert struct.unpack('<i',m.mem_read(0x140c07238,4))[0]==c['items']['cursor'],(sceneIndex,frame,'item cursor')
            assert hashlib.sha256(m.mem_read(0x1403de870,515*40)).hexdigest()==c['items']['popups'],(sceneIndex,frame,'item popups')
            assert struct.unpack('<2i',m.mem_read(0x1403de628,8))==(c['items']['popupCursor'],c['items']['smallCursor'])
            digest.update(item)

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
            
            if hashlib.sha256(fx).hexdigest()!=c['effects']['sha256']:
                wanted=bytes.fromhex(c['effects']['debug'])if c['effects']['debug']else b'';raise AssertionError((sceneIndex,frame,'effect pool',[(hex(p//0x198),hex(p%0x198),a,b)for p,(a,b)in enumerate(zip(fx,wanted))if a!=b][:40],events,c['events']))
            assert struct.unpack('<2i',m.mem_read(effectBase+0x33198,8))==(c['effects']['activeCount'],c['effects']['cursor']),(sceneIndex,frame,'effect counts');digest.update(fx)
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
            playerState=bytearray(m.mem_read(0x1404ff3a0,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',playerState,p)[0]
                    if ptr:struct.pack_into('<Q',playerState,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
                p=offset+0x100;ptr=struct.unpack_from('<Q',playerState,p)[0]
                if ptr:struct.pack_into('<Q',playerState,p,(ptr-n.manager-0x608)//64+1)
            if hashlib.sha256(playerState).hexdigest()!=c['playerSha256']:
                wanted=bytes.fromhex(c['playerDebug'])if c['playerDebug']else b'';raise AssertionError((sceneIndex,frame,'player owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(playerState,wanted))if a!=b][:40]))
            life=dict(power=struct.unpack('<H',m.mem_read(0x1404f1e88,2))[0],lives=m.mem_read(0x1404ff0f0,1)[0],bombs=m.mem_read(0x1404ff0f1,1)[0],deaths=struct.unpack('<i',m.mem_read(0x1404f1e60,4))[0]);assert life==c['life'],(sceneIndex,frame,'life',life,c['life']);digest.update(playerState)
            p=c['player'];assert m.mem_read(0x140506c38,1)[0]==p['state'],(sceneIndex,frame,'player state');assert struct.unpack('<i',m.mem_read(0x140506adc,4))[0]==p['deathBombFrames'],(sceneIndex,frame,'deathbomb');assert struct.unpack('<2i',m.mem_read(0x140506bf4,8))==(p['hitTimer']['previous'],p['hitTimer']['frame']),(sceneIndex,frame,'hit timer');assert struct.unpack('<4i',m.mem_read(0x140506d88,16))==tuple(x for t in p['hitAnimationTimers']for x in [t['previous'],t['frame']]),(sceneIndex,frame,'hit animation timers');assert list(struct.unpack('<2i',m.mem_read(0x1404ff0cc,8)))==c['grazeCounters'],(sceneIndex,frame,'graze counters');assert struct.unpack('<I',m.mem_read(0x140a6ec18,4))[0]==c['inputFlags'],(sceneIndex,frame,'input flags')
            slots=[struct.unpack('<Q',m.mem_read(owner+0x10c0e8+i*8,8))[0]for i in range(8)];assert [None if p==0 else(p-owner-8)//0x10b0 for p in slots]==c['bossSlots'],(sceneIndex,frame,'boss slots')
            spell=dict(counter=struct.unpack('<i',m.mem_read(0x140badf60,4))[0],active=bool(m.mem_read(0x140badf6c,1)[0]),id=struct.unpack('<i',m.mem_read(0x140badf68,4))[0],bonus=struct.unpack('<i',m.mem_read(0x140badf70,4))[0],finished=bool(m.mem_read(0x140aa1e8e,1)[0]),backgroundClock=struct.unpack('<i',m.mem_read(0x140509c18,4))[0],backgroundFrame=struct.unpack('<i',m.mem_read(0x140509b60,4))[0],backgroundActive=bool(m.mem_read(0x140509c1c,1)[0]),captures=struct.unpack('<i',m.mem_read(0x1404f1e68,4))[0],extraCaptures=struct.unpack('<i',m.mem_read(0x1404f1e6c,4))[0]);assert spell=={k:v for k,v in c['spell'].items()if k!='records'},(sceneIndex,frame,'spell',spell,c['spell'])
            for record in c['spell']['records']:
                actual=bytes(m.mem_read(0x1404f27c8+record['id']*0x180,0x180));assert actual.hex()==record['bytes'],(sceneIndex,frame,'spell record',record['id']);digest.update(actual)
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(sceneIndex,frame,'rng')
        assert checkedFrames==set(byFrame),(sceneIndex,'unverified checkpoints',sorted(set(byFrame)-checkedFrames))
    hitScenes=sum(s['frames'][-1]['life']['deaths']>0 for s in data['scenes']);grazeScenes=sum(s['frames'][-1]['grazeCounters'][0]>0 for s in data['scenes']);assert hitScenes and grazeScenes,'Contact fixture did not exercise both reactions'
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sourceHashes.items()),'Source changed while proof was running'
    report=dict(scope=__doc__,hitScenes=hitScenes,grazeScenes=grazeScenes,scenes=len(data['scenes']),nativeFrames=sum(s['frameLimit']for s in data['scenes']),checkpoints=sum(len(s['frames'])for s in data['scenes']),enemyStateComparisons=sum(len(f['actors'])for s in data['scenes']for f in s['frames']),stateSha256=digest.hexdigest(),sourceSha256=sourceHashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-stage-live-items-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
