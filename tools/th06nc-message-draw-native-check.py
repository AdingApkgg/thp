"""Dialog HUD draw block 3d023..3d0ad, order and stage visibility.

Real message/portrait/frame ANM states and all seven draw calls compared.
Lower renderer and GPU pixels excluded; font publication has separate proof.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/message-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readMessage}from'./shared/th06nc/message.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{messageAssetPlan}from'./shared/th06nc/message-layout.mjs';import{drawMessage}from'./shared/th06nc/message-draw.mjs';const cases=[];for(const character of [0,1])for(const frame of [0,1,60,400])for(const stage of [1,6,7])for(const id of [-1,0,1,10,11]){const refs=messageAssetPlan(1,character),bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new MessageState(readMessage(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg1.dat')),{anmBank:bank,environment:{stageIndex:stage}});state.rebind(0x3b60,0x785);state.open(character*10,{cancelProjectiles:()=>{},loadAnm:()=>{}});for(let i=0;i<frame;i++)state.tick(0,{publishText:()=>{},musicTracks:[],playMusic:()=>{}});state.v.setInt32(0x36b0,id,true);const before=Buffer.from(state.bytes).toString('hex'),calls=[];drawMessage(state,(vm,info)=>calls.push({...info,state:Buffer.from(vm.state).toString('hex')}));cases.push({refs,stage,id,before,calls,after:Buffer.from(state.bytes).toString('hex')});}console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;calls=[];digest=hashlib.sha256();parts={0x3428:('portrait',0),0x3548:('portrait',1),0x3b60:('message-frame',0),0x36b8:('message-line',0),0x37d8:('message-line',1),0x3910:('message-extra',0),0x3a30:('message-extra',1)}
    def norm(block,offset,encode=False):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
            if ptr:
                file='msgframe.anm'if offset==0x3b60 else'face00a.anm'if offset in [0x3428,0x3548]and'face00a.anm'in n.assetByFile else'face01a.anm'if offset in [0x3428,0x3548]else'text.anm';struct.pack_into('<Q',block,p,n.assetByFile[file]+ptr if encode else ptr-next(a for a,b in n.ranges if a<=ptr<b))
        p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
        if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        ptr=m.reg_read(UC_X86_REG_RDX);offset=ptr-n.owner;part,slot=parts[offset];state=bytearray(m.mem_read(ptr,288));norm(state,0);calls.append(dict(snap=bool(m.reg_read(UC_X86_REG_R8B)),space='screen',part=part,slot=slot,state=state.hex()));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1400067f0,end=0x1400067f0)
    for index,c in enumerate(cases):
        n.load_title(c['refs']);state=bytearray.fromhex(c['before'])
        for offset in parts:norm(state,offset,True)
        m.mem_write(n.owner,bytes(state));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.mem_write(0x1404f1e84,struct.pack('<i',c['stage']));m.reg_write(UC_X86_REG_RDI,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);calls.clear();m.emu_start(0x14003d023,0x14003d0ad,count=100000);assert calls==c['calls'],(index,'calls',calls[:1],c['calls'][:1]);actual=bytearray(m.mem_read(n.owner,0x4000))
        for offset in parts:norm(actual,offset)
        assert actual.hex()==c['after'];digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),drawCalls=sum(len(c['calls'])for c in cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-message-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
