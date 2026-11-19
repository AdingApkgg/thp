"""Whole player owner 68820, movement/fire/death/respawn with real ANM/shots.

Four profiles, two power levels and three initial life states, 180 frames each.
Bomb inputs excluded; drop items observed and projectile pools empty. No enemy
damage query, item entity, keyboard/browser timing or GPU equivalence claimed.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=[f'shared/th06nc/{p}.mjs'for p in ['player-init','player-state','player-update','player-input','player-motion','player-movement','player-options','player-life','player-shot-programs','player-shot-build','player-fire','player-shot-update']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const scenes=[];
for(const character of [0,1])for(const shot of [0,1])for(const power of [0,128])for(const mode of ['normal','intro','death']){
 const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const rng=new NativeRng(0xbeef,99),environment={rng,character,shot,spellPractice:mode!=='intro',playerPower:power,lives:2,bombs:3,defaultBombs:3,deathCount:0,powerItemChain:1,inputFlags:0,continueState:0,gameOverRequested:false,difficulty:0,replay:false,lifeProtection:false},player=new PlayerState({anmBank:bank,environment}),soundSlots=[-1,-1,-1],frames=[];
 if(mode==='death'){player.state=2;player.deathBombFrames=8;player.hitTimer={previous:-999,frame:0};}let previousInput=0;
 for(let frame=1;frame<=180;frame++){
  const input=(frame%120<90?1:0)|([0x10,0x40,0x20,0x80,0x90,0x60][Math.floor(frame/15)%6])|(frame%40<20?4:0),events=[];
  player.tick(input,{previousInput,messageField:-1,bounds:[8,16,368,416],soundSlots,sin:()=>0.25,cos:()=>0.75,dropItem:e=>events.push({kind:'item',...e}),cancelProjectiles:()=>{}});previousInput=input;
  if([1,2,8,9,16,30,31,60,90,120,180].includes(frame))frames.push({frame,input,events,soundSlots:[...soundSlots],environment:{deathCount:environment.deathCount,powerItemChain:environment.powerItemChain,lives:environment.lives,playerPower:environment.playerPower,inputFlags:environment.inputFlags,continueState:environment.continueState,gameOverRequested:environment.gameOverRequested,bombs:environment.bombs},rng:{seed:rng.seed,count:rng.count},state:Buffer.from(player.bytes).toString('hex'),sha256:createHash('sha256').update(player.bytes).digest('hex')});
 }scenes.push({ref,character,shot,power,mode,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0;events=[]
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400426e0:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),critical=bool(m.reg_read(UC_X86_REG_R9D))));m.reg_write(UC_X86_REG_RAX,0)
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be071,0x1402be07d,0x1400426e0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(address,n.stack+0xf000,count=1000000)
    for sceneIndex,scene in enumerate(scenes):
        n.load_title([scene['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm));m.mem_write(n.vm+0x36b0,struct.pack('<i',-1));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,bytes([scene['mode']!='intro']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f1e88,struct.pack('<H',scene['power']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x1404ff0e0,struct.pack('<4f',8,16,368,416));m.mem_write(0x1404f1e60,bytes(4));m.mem_write(0x1404ff0dd,b'\1');m.mem_write(0x1404ff0f0,bytes([2,3,0]));m.mem_write(0x1404f27c4,b'\0');m.mem_write(0x140a6ec18,bytes(4));m.mem_write(0x1404f27b1,b'\0');m.mem_write(0x1404f27b4,b'\0');m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x1404f27c0,bytes(4));m.mem_write(0x140c21de1,b'\3');m.mem_write(0x1403ec2a8,bytes(640*0x620));m.mem_write(0x1404e12b8,bytes(64*0x298));run(0x140068160)
        if scene['mode']=='death':m.mem_write(n.owner+0x7898,b'\2');m.mem_write(n.owner+0x773c,struct.pack('<i',8));m.mem_write(n.owner+0x7854,struct.pack('<2i',-999,0))
        last=0;previous=0
        for c in scene['frames']:
            for frame in range(last+1,c['frame']+1):
                current=(1 if frame%120<90 else 0)|[0x10,0x40,0x20,0x80,0x90,0x60][frame//15%6]|(4 if frame%40<20 else 0);m.mem_write(0x140a6ec60,struct.pack('<2I',current,previous));previous=current;events.clear();run(0x140068820)
            last=c['frame'];actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(c['state']);assert actual==wanted,(sceneIndex,scene['character'],scene['shot'],scene['power'],scene['mode'],last,[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]);assert events==c['events'],(sceneIndex,last,'events');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];
            env=dict(deathCount=struct.unpack('<i',m.mem_read(0x1404f1e60,4))[0],powerItemChain=m.mem_read(0x1404ff0dd,1)[0],lives=m.mem_read(0x1404ff0f0,1)[0],playerPower=struct.unpack('<H',m.mem_read(0x1404f1e88,2))[0],inputFlags=struct.unpack('<I',m.mem_read(0x140a6ec18,4))[0],continueState=struct.unpack('<b',m.mem_read(0x1404ff0f2,1))[0],gameOverRequested=bool(m.mem_read(0x1404f27b1,1)[0]),bombs=m.mem_read(0x1404ff0f1,1)[0]);assert env==c['environment'],(sceneIndex,last,'environment',env,c['environment']);digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*180,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
