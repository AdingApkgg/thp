"""Player shot owner allocation/activation and fire clock through original callbacks.

Full owner, ANM binding, cooldowns, sound and RNG compared. Shared trig inputs;
subsequent shot motion and damage queries excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/player-fire.mjs','shared/th06nc/player-init.mjs','shared/th06nc/player-shot-programs.mjs','shared/th06nc/player-shot-build.mjs','shared/th06nc/player-state.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{firePlayerShots}from'./shared/th06nc/player-fire.mjs';const scenes=[];
for(const character of [0,1])for(const shot of [0,1]){const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const cases=[];
for(const power of [0,8,16,32,48,64,80,96,128])for(const clock of [-1,0,1,4,8,15,29,30])for(const occupied of [0,79,80])for(const bombActive of [false,true]){
 const rng=new NativeRng(0xbeef,99),player=new PlayerState({anmBank:bank,environment:{rng,character,shot,spellPractice:true,playerPower:power}});player.v.setInt32(0x40c,clock,true);player.v.setInt32(0x408,cases.length%3===0?clock:-999,true);player.v.setUint8(0x9ec8,Number(bombActive));for(let i=0;i<occupied;i++)player.v.setUint16(0x420+i*0x170,1,true);const soundSlots=[[-1,-1,-1],[1,-1,-1],[3,-1,-1],[1,2,3]][cases.length%4].slice(),initialSound=[...soundSlots],soundDisabled=cases.length%7===0,result=firePlayerShots(player,{soundSlots,soundDisabled,sin:()=>0.25,cos:()=>0.75});cases.push({power,clock,occupied,bombActive,previous:cases.length%3===0?clock:-999,initialSound,soundDisabled,result,soundSlots,rng,sha256:createHash('sha256').update(player.bytes).digest('hex')});
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
            m.mem_write(n.owner,initial);m.mem_write(n.owner+0x408,struct.pack('<2i',c['previous'],c['clock']));m.mem_write(n.owner+0x9ec8,bytes([c['bombActive']]));
            for slot in range(c['occupied']):m.mem_write(n.owner+0x420+slot*0x170,b'\1\0')
            m.mem_write(0x1404f1e88,struct.pack('<H',c['power']));m.mem_write(0x140509670,struct.pack('<3i',*c['initialSound']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef))
            m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R12D,1);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140069b7e,0x140069c9f,count=1000000);actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(actual).hexdigest()==c['sha256'],(sceneIndex,c['power'],c['clock'],c['occupied'],c['bombActive']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,profiles=4,records=193,cases=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-fire-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
