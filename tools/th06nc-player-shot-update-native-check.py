"""Actual 80-slot player shot update loop, homing, acceleration and lasers.

Four profiles, six power levels and three aim targets across 120 frames. Real
ANM updates/cooldown interrupts; fixed initial trig. Damage queries excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/player-init.mjs','shared/th06nc/player-state.mjs','shared/th06nc/player-shot-programs.mjs','shared/th06nc/player-shot-build.mjs','shared/th06nc/player-fire.mjs','shared/th06nc/player-shot-update.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{firePlayerShots}from'./shared/th06nc/player-fire.mjs';import{advancePlayerShots}from'./shared/th06nc/player-shot-update.mjs';const scenes=[];
for(const character of [0,1])for(const shot of [0,1])for(const power of [0,8,16,32,64,128])for(const target of [[192,100],[-999,-999],[0,0]]){
 const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const rng=new NativeRng(0xbeef,99),player=new PlayerState({anmBank:bank,environment:{rng,character,shot,spellPractice:true,playerPower:power}});for(const p of [0x7880,0x788c]){player.v.setFloat32(p,100,true);player.v.setFloat32(p+4,400,true);}player.v.setInt32(0x40c,0,true);firePlayerShots(player,{sin:()=>0.25,cos:()=>0.75});const frames=[];
 for(let frame=1;frame<=120;frame++){player.v.setFloat32(0x7740,target[0],true);player.v.setFloat32(0x7744,target[1],true);advancePlayerShots(player);if([1,2,10,30,60,120].includes(frame))frames.push({frame,rng:{seed:rng.seed,count:rng.count},state:Buffer.from(player.bytes).toString('hex'),sha256:createHash('sha256').update(player.bytes).digest('hex')});}scenes.push({ref,character,shot,power,target,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0
    def hook(m,a,size,u):
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for sceneIndex,scene in enumerate(scenes):
        n.load_title([scene['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f1e88,struct.pack('<H',scene['power']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x140068160,n.stack+0xf000,count=1000000)
        for p in [0x7880,0x788c]:m.mem_write(n.owner+p,struct.pack('<2f',100,400))
        m.mem_write(n.owner+0x40c,bytes(4));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R12D,1);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140069b7e,0x140069c9f,count=1000000);last=0
        for c in scene['frames']:
            for frame in range(last+1,c['frame']+1):
                m.mem_write(n.owner+0x7740,struct.pack('<2f',*scene['target']));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R12D,1);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_XMM11,0);m.reg_write(UC_X86_REG_XMM8,int.from_bytes(struct.pack('<f',1),'little'));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140069740,0x140069b09,count=1000000)
            last=c['frame'];actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(c['state']);assert actual==wanted,(sceneIndex,scene['character'],scene['shot'],scene['power'],scene['target'],last,[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*120,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-shot-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
