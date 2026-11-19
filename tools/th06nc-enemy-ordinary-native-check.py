"""Continuous ordinary enemy manager update with actual ECL and ANM execution.

Timeline, trig, player collision/damage and bullet emission are supplied observed
services. Ordinary death is included; boss, actual items/effects/projectiles, player simulation and GPU are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';import{EnemyPool}from'./shared/th06nc/enemy-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{tickOrdinaryEnemy}from'./shared/th06nc/enemy-ordinary.mjs';
const plan=stageAssetPlan(1),resources=new Map(plan.enemyAnimations.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+r.file))])),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl')),scenes=[],hex=bytes=>Buffer.from(bytes).toString('hex'),vector=values=>{const b=Buffer.alloc(values.length*4);values.forEach((x,i)=>b.writeFloatLE(x,i*4));return hex(b);};
for(const position of [[60,-32,0],[100,100,0],[390,100,0]])for(const mirror of [false,true])for(const mode of [0,1,2,3,4,5,6,7,8,9,10,11]){
const config={position,mirror,damage:[0,20,80,20,20,20,20,20,20,0,0,0][mode],body:mode===1?1:0,critical:mode>=3&&mode<=4,damageMode:mode>=2&&mode<=4,criticalDamageEnabled:mode===4},events=[],soundSlots=[-1,-1,-1],environment={difficulty:1,rank:0,playerPosition:[192,400,0],rng:new NativeRng(0xbeef,99),score:0n,enemyDeathCount:0,itemDropIndex:0,aimTarget:[0,-1000,0],damageMode:config.damageMode,criticalDamageEnabled:config.criticalDamageEnabled},bank=new AnmBank();loadStageEnemyBank(bank,resources,1);
const pool=new EnemyPool(program,{anmBank:bank,environment,soundSlots,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,fireBullets:(e,s)=>events.push({kind:'shot',descriptor:hex(s)})}),entry=pool.spawn({sub:0,position,life:mode>=5&&mode<=8?5:30000,item:-1,score:300});if(mode>=5&&mode<=8)entry.v.setUint8(0xbd,(entry.v.getUint8(0xbd)&31)|((mode-5)<<5));if(mode===9){entry.v.setInt32(0xa0,40000,true);entry.v.setInt32(0xa4,0,true);}if(mode>=10){entry.v.setInt32(0xc54,5,true);entry.v.setInt32(0xc58,0,true);entry.v.setUint8(0xbe,mode===10?16:0);}if(mirror)entry.v.setUint8(0xbc,entry.v.getUint8(0xbc)|64);
const initial=hex(entry.enemy),rngInitial={seed:environment.rng.seed,count:environment.rng.count},frames=[];
for(let frame=1;frame<=240;frame++){
 events.length=0;const sourceBounds=[...entry.enemyAnms.get(0x108).boundSprite.extra];const activeCount=(entry.v.getUint8(0xbc)&128)?1:0;
 const result=tickOrdinaryEnemy(entry,{environment,bodyCollision:(e,box)=>{events.push({kind:'body',position:hex(e.enemy.subarray(0xb0,0xbc)),box:vector(box)});return config.body;},cancelBullets:()=>events.push({kind:'cancel'}),spawnEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e}),damageQuery:e=>{events.push({kind:'damage',position:hex(e.enemy.subarray(0xb0,0xbc)),box:hex(e.enemy.subarray(0x2c0,0x2cc))});return {damage:config.damage,critical:config.critical};}});
 if((position[0]===60&&!mirror&&mode===0)||[1,2,4,34,35,39,40,120,144,200,240].includes(frame))frames.push({frame,sourceBounds,activeCount,result,after:hex(entry.enemy),events:[...events],rng:{seed:environment.rng.seed,count:environment.rng.count},score:String(environment.score),aimTarget:vector(environment.aimTarget),soundSlots:[...soundSlots],enemyDeathCount:environment.enemyDeathCount,itemDropIndex:environment.itemDropIndex});
}
scenes.push({config,initial,rngInitial,frames});}
console.log(JSON.stringify({plan,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['plan']['enemyAnimations']);m=n.m;owner=0x140aa1e90;enemy=owner+8;programBase=n.assets+0x100000;table=n.vm+0x8000;digest=hashlib.sha256();events=[];config=None
    program=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl').read_bytes();m.mem_write(programBase,program)
    for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(n.owner+0x36b0,bytes(4));m.mem_write(0x1404f27c0,struct.pack('<i',1));m.mem_write(0x1404ff27c,bytes(4));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x1404f27b9,b'\0')
    def hook(m,a,size,u):
        if a==0x140037039:events.append(dict(kind='cancel'));return
        if a==0x140036260:m.reg_write(UC_X86_REG_RAX,0)
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',{0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a]),'little'))
        elif a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()));m.reg_write(UC_X86_REG_RAX,0)
        elif a in [0x14006a980,0x140069d00]:
            events.append(dict(kind='body'if a==0x14006a980 else'damage',position=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),12)).hex(),box=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),12)).hex()))
            if a==0x140069d00:m.mem_write(m.reg_read(UC_X86_REG_R9),bytes([config['critical']]))
            m.reg_write(UC_X86_REG_RAX,config['body']if a==0x14006a980 else config['damage'])
        elif a in [0x14002b0d0,0x1400426e0]:
            position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
            if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]))
            else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))))
            m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x1402bcf20:pass
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for sceneIndex,scene in enumerate(data['scenes']):
        config=scene['config'];m.mem_write(owner,bytes(0x10d1e0));state=bytearray.fromhex(scene['initial']);ptr=struct.unpack_from('<Q',state,0x88)[0];struct.pack_into('<Q',state,0x88,programBase+ptr)
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',state,0x108+p)[0]
            if ptr:struct.pack_into('<Q',state,0x108+p,n.assets+ptr)
        ptr=struct.unpack_from('<Q',state,0x208)[0]
        if ptr:struct.pack_into('<Q',state,0x208,n.manager+0x608+(ptr-1)*64)
        m.mem_write(enemy,bytes(state));m.mem_write(owner+0x10c0d0,struct.pack('<i',config['damageMode']));m.mem_write(owner+0x10c0d4,bytes([config['criticalDamageEnabled']]));m.mem_write(0x140a6ec40,struct.pack('<IH',scene['rngInitial']['count'],scene['rngInitial']['seed']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404f2798,bytes(8));m.mem_write(0x140506ae0,struct.pack('<3f',0,-1000,0));byFrame={f['frame']:f for f in scene['frames']}
        for frame in range(1,241):
            events.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(0x1400373b0,n.stack+0xf000,count=1000000)
            if frame not in byFrame:continue
            c=byFrame[frame];actual=bytearray(m.mem_read(enemy,0x10b0));ptr=struct.unpack_from('<Q',actual,0x88)[0];struct.pack_into('<Q',actual,0x88,ptr-programBase)
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,0x108+p)[0]
                if ptr:struct.pack_into('<Q',actual,0x108+p,ptr-n.assets)
            ptr=struct.unpack_from('<Q',actual,0x208)[0]
            if ptr:struct.pack_into('<Q',actual,0x208,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(sceneIndex,frame,c['sourceBounds'],struct.unpack('<2f',m.mem_read(struct.unpack('<Q',m.mem_read(enemy+0x208,8))[0]+0x1c,8)),diff)
            assert events==c['events'],(sceneIndex,frame,events,c['events']);assert struct.unpack('<i',m.mem_read(owner,4))[0]==c['activeCount'],(sceneIndex,frame,'active count')
            assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['score'],(sceneIndex,frame,'score');assert bytes(m.mem_read(0x140506ae0,12)).hex()==c['aimTarget'],(sceneIndex,frame,'aim target');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(sceneIndex,frame,'sounds')
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(sceneIndex,frame,'rng');assert struct.unpack('<i',m.mem_read(owner+0x10c0bc,4))[0]==frame;assert struct.unpack('<HH',m.mem_read(owner+4,4))==(c['enemyDeathCount'],c['itemDropIndex']),(sceneIndex,frame,'item cycle');digest.update(actual)
    report=dict(scope=__doc__,scenes=len(data['scenes']),nativeFrames=len(data['scenes'])*240,checkpoints=sum(len(s['frames'])for s in data['scenes']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/enemy-ordinary.mjs','shared/th06nc/enemy-death.mjs','shared/th06nc/enemy-phase.mjs','shared/th06nc/enemy-pool.mjs','shared/th06nc/enemy-position.mjs','shared/th06nc/enemy-animation.mjs','shared/th06nc/ecl-tick.mjs','shared/th06nc/ecl-command.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-ordinary-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
