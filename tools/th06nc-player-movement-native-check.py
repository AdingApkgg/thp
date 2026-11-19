"""Continuous moving-player section with real character ANM rebindings.

Four profiles, all 256 low input combinations in sequence. Full player owner
and RNG compared. Life/option/shot updates and ordinary ANM ticks excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/player-init.mjs','shared/th06nc/player-input.mjs','shared/th06nc/player-motion.mjs','shared/th06nc/player-movement.mjs','shared/th06nc/player-state.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const scenes=[];for(const character of [0,1])for(const shot of [0,1]){const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const rng=new NativeRng(0xbeef,99),player=new PlayerState({anmBank:bank,environment:{rng,character,shot,spellPractice:true}}),frames=[];for(let input=0;input<256;input++){player.move(input,{bounds:[8,16,368,416]});frames.push({input,position:player.position,rng:{seed:rng.seed,count:rng.count},state:Buffer.from(player.bytes).toString('hex'),sha256:createHash('sha256').update(player.bytes).digest('hex')});}scenes.push({ref,character,shot,frames});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();frames=0
    for sceneIndex,scene in enumerate(scenes):
        n.load_title([scene['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404ff0e0,struct.pack('<4f',8,16,368,416));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x140068160,n.stack+0xf000,count=1000000)
        for c in scene['frames']:
            for reg,value in [(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R13,n.manager),(UC_X86_REG_R11D,c['input']),(UC_X86_REG_R12D,1),(UC_X86_REG_R15D,8),(UC_X86_REG_R8D,5),(UC_X86_REG_EBX,2),(UC_X86_REG_ESI,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
            m.reg_write(UC_X86_REG_XMM11,0);m.emu_start(0x140069066,0x1400694f6,count=1000000);actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(c['state']);assert actual==wanted,(sceneIndex,c['input'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);frames+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,scenes=len(scenes),frames=frames,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-movement-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
