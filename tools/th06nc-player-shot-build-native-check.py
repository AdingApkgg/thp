"""All original player shot records through actual generic constructor wrappers.

Full owner, ANM binding, cooldowns, sound and RNG compared. Shared trig inputs;
owner allocation/activation, subsequent shot motion and damage queries excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/player-init.mjs','shared/th06nc/player-shot-programs.mjs','shared/th06nc/player-shot-build.mjs','shared/th06nc/player-state.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{playerShotBand,buildPlayerShot}from'./shared/th06nc/player-shot-build.mjs';const scenes=[];
for(const character of [0,1])for(const shot of [0,1]){const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const cases=[];
for(const power of [0,8,16,32,48,64,80,96,128])for(let index=0;index<playerShotBand(character,shot,power).records.length;index++)for(const clock of [0,1,4,8,15,16,29])for(const cooldown of [0,1]){
 const rng=new NativeRng(0xbeef,99),player=new PlayerState({anmBank:bank,environment:{rng,character,shot,spellPractice:true,playerPower:power}});player.v.setInt32(0x79ec,cooldown,true);player.v.setInt32(0x79f4,cooldown,true);const soundSlots=[[-1,-1,-1],[1,-1,-1],[3,-1,-1],[1,2,3]][cases.length%4].slice(),initialSound=[...soundSlots],soundDisabled=cases.length%7===0,result=buildPlayerShot(player,11,index,clock,{soundSlots,soundDisabled,sin:()=>0.25,cos:()=>0.75});cases.push({power,index,clock,cooldown,initialSound,soundDisabled,result,soundSlots,rng,shotState:Buffer.from(player.bytes.subarray(0x410+11*0x170,0x410+12*0x170)).toString('hex'),sha256:createHash('sha256').update(player.bytes).digest('hex')});
}scenes.push({ref,character,shot,cases});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0
    def hook(m,a,size,u):
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def call(address):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(address,n.stack+0xf000,count=1000000)
    for sceneIndex,scene in enumerate(scenes):
        n.load_title([scene['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.reg_write(UC_X86_REG_RCX,n.owner);call(0x140068160);initial=bytes(m.mem_read(n.owner,0xa2b8))
        for c in scene['cases']:
            m.mem_write(n.owner,initial);m.mem_write(n.owner+0x79ec,struct.pack('<i',c['cooldown']));m.mem_write(n.owner+0x79f4,struct.pack('<i',c['cooldown']));m.mem_write(0x1404f1e88,struct.pack('<H',c['power']));m.mem_write(0x140509670,struct.pack('<3i',*c['initialSound']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef))
            for reg,value in [(UC_X86_REG_RCX,n.owner),(UC_X86_REG_RDX,n.owner+0x410+11*0x170),(UC_X86_REG_R8D,c['index']),(UC_X86_REG_R9D,c['clock'])]:m.reg_write(reg,value)
            call(0x14006a840+sceneIndex*32);actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,0x428+11*0x170]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(c['shotState']);got=actual[0x410+11*0x170:0x410+12*0x170];assert hashlib.sha256(actual).hexdigest()==c['sha256'],(sceneIndex,c['power'],c['index'],c['clock'],c['cooldown'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(got,wanted))if a!=b][:20]);assert m.reg_read(UC_X86_REG_EAX)==c['result']&0xffffffff;assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,profiles=4,records=193,cases=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-shot-build-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
