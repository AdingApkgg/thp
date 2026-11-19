"""Original 69d00 query: shot/splash/laser and bomb rectangles hitting enemies.

Real shot/impact ANM; effect publication observed. Repeated queries compare
full owner bytes, damage, critical flag, effects and RNG. Item/GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=[f'shared/th06nc/{p}.mjs'for p in ['player-init','player-state','player-shot-programs','player-shot-build','player-fire','player-damage']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{firePlayerShots}from'./shared/th06nc/player-fire.mjs';import{queryPlayerDamage}from'./shared/th06nc/player-damage.mjs';const scenes=[];
for(const character of [0,1])for(const shot of [0,1])for(const power of [0,32,128])for(const position of [[192,384,0],[0,0,0],[100,100,0],[208,400,0]])for(const size of [[1,1],[16,16],[64,64]])for(const bombActive of [false,true])for(const areas of [false,true]){
 const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const rng=new NativeRng(0xbeef,99),player=new PlayerState({anmBank:bank,environment:{rng,character,shot,spellPractice:true,playerPower:power}});player.v.setInt32(0x40c,0,true);firePlayerShots(player,{sin:()=>0.25,cos:()=>0.75});player.v.setUint8(0x9ec8,Number(bombActive));player.v.setUint8(0x7718,7);
 if(areas)for(let i=0;i<2;i++){player.v.setFloat32(i*12,i===0?192:0,true);player.v.setFloat32(i*12+4,i===0?384:0,true);player.v.setFloat32(0x180+i*12,32,true);player.v.setFloat32(0x184+i*12,24,true);player.v.setInt32(0x300+i*4,i===0?7:11,true);}
 const queries=[];for(let repeat=0;repeat<3;repeat++){const events=[],result=queryPlayerDamage(player,{position,size},{spawnEffect:e=>events.push(e)});queries.push({result,events,rng:{seed:rng.seed,count:rng.count},sha256:createHash('sha256').update(player.bytes).digest('hex')});}scenes.push({ref,character,shot,power,position,size,bombActive,areas,queries});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();events=[];checked=0
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14002b0d0:events.append(dict(type=m.reg_read(UC_X86_REG_EDX),count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0],position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12)))));m.reg_write(UC_X86_REG_RAX,0)
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.75 if a==0x1402be071 else 0.25),'little'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402be071,0x1402be07d,0x14002b0d0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(address,n.stack+0xf000,count=1000000)
    for sceneIndex,scene in enumerate(scenes):
        n.load_title([scene['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x1404f1e80,bytes([scene['character'],scene['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f1e88,struct.pack('<H',scene['power']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.reg_write(UC_X86_REG_RCX,n.owner);run(0x140068160);m.mem_write(n.owner+0x40c,bytes(4));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R12D,1);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140069b7e,0x140069c9f,count=1000000);m.mem_write(n.owner+0x9ec8,bytes([scene['bombActive']]));m.mem_write(n.owner+0x7718,b'\7')
        if scene['areas']:
            for i in range(2):m.mem_write(n.owner+i*12,struct.pack('<2f',192 if i==0 else 0,384 if i==0 else 0));m.mem_write(n.owner+0x180+i*12,struct.pack('<2f',32,24));m.mem_write(n.owner+0x300+i*4,struct.pack('<i',7 if i==0 else 11))
        m.mem_write(n.vm,struct.pack('<3f',*scene['position']));m.mem_write(n.vm+16,struct.pack('<2f',*scene['size']))
        for queryIndex,c in enumerate(scene['queries']):
            events.clear();m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8,n.vm+16);m.reg_write(UC_X86_REG_R9,n.vm+32);run(0x140069d00);actual=bytearray(m.mem_read(n.owner,0xa2b8))
            for offset in [0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]:
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(actual).hexdigest()==c['sha256'],(sceneIndex,scene['character'],scene['shot'],scene['power'],scene['position'],scene['size'],scene['bombActive'],scene['areas'],queryIndex,'owner');value=m.reg_read(UC_X86_REG_EAX);value=value-0x100000000 if value>=0x80000000 else value;assert dict(damage=value,critical=bool(m.mem_read(n.vm+32,1)[0]))==c['result'],(sceneIndex,queryIndex,'result');assert events==c['events'],(sceneIndex,queryIndex,'effects',events,c['events']);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual);checked+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,scenes=len(scenes),queries=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-damage-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
