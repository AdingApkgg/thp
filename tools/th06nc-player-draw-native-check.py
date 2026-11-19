"""Player owner draw 6a254..6a3ff: shots, main sprite, options and visibility.

Full owner bytes and observed 2D draw calls compared, including default environment spellResultVisible mapping for death/respawn visibility. Bomb/GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{PlayerState}from'./shared/th06nc/player-state.mjs';import{playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{drawPlayer}from'./shared/th06nc/player-draw.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const character of [0,1])for(const shot of [0,1])for(const frame of [0,45])for(const state of [0,1,2,3])for(const hideDuringRespawn of [false,true])for(const gameOver of [false,true]){
 const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const player=new PlayerState({anmBank:bank,environment:{character,shot,playerPower:128,spellPractice:true,spellResultVisible:hideDuringRespawn}});for(let i=0;i<frame;i++)player.tick(1|4,{cancelProjectiles:()=>{},dropItem:()=>{}});player.state=state;const before=hex(player.bytes),calls=[];drawPlayer(player,(vm,info)=>calls.push({...info,state:hex(vm.state)}),{gameOver});cases.push({ref,before,calls,hideDuringRespawn,gameOver,sha256:createHash('sha256').update(player.bytes).digest('hex')});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;calls=[];digest=hashlib.sha256()
    def normalize(block,offset,encode=False):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:struct.pack_into('<Q',block,p,n.assets+ptr if encode else ptr-n.assets)
        p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
        if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        ptr=m.reg_read(UC_X86_REG_RDX);offset=ptr-n.owner
        if offset==0x78c8:part,slot='player',0
        elif offset in [0x9f38,0xa058]:part,slot='option',(offset-0x9f38)//0x120
        else:part,slot='player-shot',(offset-0x428)//0x170
        state=bytearray(m.mem_read(ptr,288));normalize(state,0);calls.append(dict(snap=bool(m.reg_read(UC_X86_REG_R8B)),space='screen',part=part,slot=slot,state=state.hex()));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1400067f0,end=0x1400067f0)
    offsets=[0x78c8,0x9f38,0xa058,*[0x428+i*0x170 for i in range(80)]]
    for index,c in enumerate(cases):
        n.load_title([c['ref']]);state=bytearray.fromhex(c['before'])
        for offset in offsets:normalize(state,offset,True)
        m.mem_write(n.owner,bytes(state));m.mem_write(0x1404f27b6,bytes([c['hideDuringRespawn']]));m.mem_write(0x1404f27b1,bytes([c['gameOver']]));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);calls.clear();m.emu_start(0x14006a254,0x14006a3ff,count=100000);assert calls==c['calls'],(index,'calls');actual=bytearray(m.mem_read(n.owner,len(state)))
        for offset in offsets:normalize(actual,offset)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'owner');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),drawCalls=sum(len(c['calls'])for c in cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
