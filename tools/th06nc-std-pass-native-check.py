"""Both native background draw tasks, including spell overlay initialization.

Observe setup/render-state/layer/fog/cover/overlay calls and compare complete
owner bytes. All seven real effect ANMs; overlay modes, clocks, base hiding,
pending ANM bind and fog refresh flags. GPU calls/layer geometry are services.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/std-state.mjs','shared/th06nc/std-pass.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readStd}from'./shared/th06nc/std.mjs';import{initializeStd,stdAssetPlan}from'./shared/th06nc/std-state.mjs';import{stageEffectAssetPlan}from'./shared/th06nc/common-layout.mjs';import{drawStdPass}from'./shared/th06nc/std-pass.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');for(let stage=1;stage<=7;stage++){const refs=[stdAssetPlan(stage),stageEffectAssetPlan(stage)],bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const program=readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),cases=[];for(const pass of [0,1])for(const mode of [0,1,2])for(const frame of [0,59,60,61])for(const pending of [0,1])for(const hideBase of [false,true])for(const fogRefresh of [0,1]){const state=initializeStd(program,{anmBank:bank}),v=state.v;v.setInt32(0xb8,mode,true);v.setInt32(0,frame,true);v.setUint8(0xbc,pending);v.setUint8(0x9c,fogRefresh);v.setUint32(0x40,0xff123456,true);const initial=hex(state.owner),events=[],result=drawStdPass(state,pass,{hideBase,setupCamera:r=>events.push({kind:'setup',...r}),renderState:r=>events.push({kind:'state',...r}),backgroundMode:value=>events.push({kind:'backgroundMode',value}),drawLayer:layer=>events.push({kind:'layer',layer}),setFogColor:rgb=>events.push({kind:'fogColor',rgb}),setFogRange:values=>events.push({kind:'fogRange',values}),drawCover:r=>events.push({kind:'cover',...r}),drawOverlay:vm=>events.push({kind:'overlay',sha256:sha(vm.state)}),setTextureFactor:r=>events.push({kind:'factor',...r})});cases.push({pass,hideBase,initial,events,result,after:hex(state.owner)});}scenes.push({stage,refs,cases});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();checked=0
    def normalize(data):
        for field in [0xf0,0xf8]:
            p=0xd0+field;ptr=struct.unpack_from('<Q',data,p)[0]
            if ptr:struct.pack_into('<Q',data,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
        p=0xd0+0x100;ptr=struct.unpack_from('<Q',data,p)[0]
        if ptr:struct.pack_into('<Q',data,p,(ptr-n.manager-0x608)//64+1)
    def floats(regs):return [struct.unpack('<f',m.reg_read(r).to_bytes(16,'little')[:4])[0]for r in regs]
    def hook(m,a,size,u):
        if a==0x14007af40:events.append(dict(kind='setup',minZ=floats([UC_X86_REG_XMM1])[0],maxZ=floats([UC_X86_REG_XMM2])[0]))
        elif a in [0x140098100,0x140098310,0x1400982c0]:events.append(dict(kind='state',name={0x140098100:'depthTest',0x140098310:'cull',0x1400982c0:'depthWrite'}[a],value=m.reg_read(UC_X86_REG_ECX)))
        elif a==0x140078cb0:events.append(dict(kind='layer',layer=m.reg_read(UC_X86_REG_EDX)))
        elif a==0x1400969c0:events.append(dict(kind='fogColor',rgb=[m.reg_read(r)for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_R8D]]))
        elif a==0x140096b00:events.append(dict(kind='fogRange',values=floats([UC_X86_REG_XMM0,UC_X86_REG_XMM1])))
        elif a==0x140075be0:events.append(dict(kind='cover',rect=list(struct.unpack('<4f',m.mem_read(m.reg_read(UC_X86_REG_RCX),16))),color=m.reg_read(UC_X86_REG_EDX)))
        elif a==0x1400974e0:events.append(dict(kind='factor',stage=m.reg_read(UC_X86_REG_ECX),operation=m.reg_read(UC_X86_REG_EDX),color=m.reg_read(UC_X86_REG_R8D)))
        elif a==0x1400067f0:
            data=bytearray(m.mem_read(n.owner,0x220));normalize(data);events.append(dict(kind='overlay',sha256=hashlib.sha256(data[0xd0:0x1f0]).hexdigest()))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14007af40,0x140098100,0x140098310,0x1400982c0,0x140078cb0,0x1400969c0,0x140096b00,0x140075be0,0x1400974e0,0x1400067f0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.hook_add(UC_HOOK_MEM_WRITE,lambda m,access,address,size,value,u:events.append(dict(kind='backgroundMode',value=bool(value))),begin=n.manager+0x27100,end=n.manager+0x27100)
    for s in scenes:
        n.load_title(s['refs']);m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm));m.mem_write(n.vm,bytes(288))
        for c in s['cases']:
            m.mem_write(n.owner,bytes.fromhex(c['initial']));m.mem_write(n.vm+0x34,struct.pack('<h',0 if c['hideBase']else-1));m.mem_write(n.vm+0xc4,struct.pack('<I',0x4000 if c['hideBase']else 0));events.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140078290 if c['pass']==0 else 0x140078390,n.stack+0xf000,count=1000000)
            assert m.reg_read(UC_X86_REG_EAX)==c['result'];assert events==c['events'],(s['stage'],checked,c['pass'],'events',events,c['events']);actual=bytearray(m.mem_read(n.owner,0x220));normalize(actual);wanted=bytes.fromhex(c['after']);assert actual==wanted,(s['stage'],checked,'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]);digest.update(actual);checked+=1
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,stages=len(scenes),cases=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-std-pass-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
