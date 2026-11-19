"""Seven backgrounds with repeated spell begin/end, pause and draw cycles.

Compare complete owner including overlay ANM, base ANM pool, descriptors,
direction and fog requests. Native update 77bb0 and both draw tasks execute;
layer geometry and GPU transport are observed service boundaries.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/std.mjs','shared/th06nc/std-state.mjs','shared/th06nc/std-update.mjs','shared/th06nc/std-pass.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{stageEffectAssetPlan}from'./shared/th06nc/common-layout.mjs';import{drawStdPass,beginStdSpell,endStdSpell}from'./shared/th06nc/std-pass.mjs';import{createHash}from'node:crypto';import{advanceStd}from'./shared/th06nc/std-update.mjs';import{readFileSync}from'node:fs';import{readStd}from'./shared/th06nc/std.mjs';import{initializeStd,stdAssetPlan}from'./shared/th06nc/std-state.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');for(let stage=1;stage<=7;stage++){const ref=stdAssetPlan(stage),refs=[ref,stageEffectAssetPlan(stage)],bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const program=readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),state=initializeStd(program,{anmBank:bank});const frames=[];state.direction=[0,0,0];for(let frame=1;frame<=500;frame++){const events=[],paused=(frame>=80&&frame<=82)||frame===10000;if(frame%180===0)state.v.setUint8(0x68,1);if(frame===30||frame===250)beginStdSpell(state);if(frame===200||frame===400)endStdSpell(state);const result=advanceStd(state,{paused,setFogColor:rgb=>events.push({kind:'color',rgb}),setFogRange:values=>events.push({kind:'range',values})});for(const pass of [0,1])drawStdPass(state,pass,{setFogColor:rgb=>events.push({kind:'color',rgb}),setFogRange:values=>events.push({kind:'range',values})});if(frame<4||frame%4===0||[79,80,81,82,83,180,9999,10000,10001].includes(frame))frames.push({frame,result,owner:hex(state.owner),fileSha:sha(state.bytes),poolSha:sha(state.storage),direction:[...state.direction],events});}scenes.push({stage,ref,refs,frames,objects:program.objectCount,primitives:program.primitiveCount,instances:program.instances.length,instructions:program.instructions.length,bytes:hex(state.bytes),storage:hex(state.storage),owner:hex(state.owner)});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;rawBase=n.assets+0x100000;table=n.owner+0x400;pool=n.owner+0x1000;requests=[];allocs=[];fog=[];digest=hashlib.sha256()
    def string(ptr):return bytes(m.mem_read(ptr,128)).split(b'\0')[0].decode()
    def hook(m,a,size,u):
        if a in [0x14007af40,0x140098100,0x140098310,0x1400982c0,0x140078cb0,0x140075be0,0x1400974e0,0x1400067f0]:pass
        elif a==0x1400020b0:requests.append(dict(kind='anm',file=string(m.reg_read(UC_X86_REG_R8)),slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_EAX,0)
        elif a==0x1400387a0:requests.append(dict(kind='std',file=string(m.reg_read(UC_X86_REG_RCX))));m.reg_write(UC_X86_REG_RAX,rawBase)
        elif a==0x1402bd4a0:
            size=m.reg_read(UC_X86_REG_RCX);ptr=table if not allocs else pool;allocs.append(size);m.mem_write(ptr,bytes(size));m.reg_write(UC_X86_REG_RAX,ptr)
        elif a==0x1400969c0:fog.append(dict(kind='color',rgb=[m.reg_read(r)for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_R8D]]))
        elif a==0x140096b00:fog.append(dict(kind='range',values=[struct.unpack('<f',m.reg_read(r).to_bytes(16,'little')[:4])[0]for r in [UC_X86_REG_XMM0,UC_X86_REG_XMM1]]))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14007af40,0x140098100,0x140098310,0x1400982c0,0x140078cb0,0x140075be0,0x1400974e0,0x1400067f0,0x1400020b0,0x1400387a0,0x1402bd4a0,0x1400969c0,0x140096b00]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for s in scenes:
        n.load_title(s['refs']);m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm));m.mem_write(n.vm,bytes(288));m.mem_write(n.vm+0x34,struct.pack('<h',-1));m.mem_write(rawBase,(ROOT/f"runtimes/th06nc/artifacts/scripts/th06ST.dat/stage{s['stage']}.std").read_bytes());m.mem_write(n.owner,bytes(0x220));m.mem_write(0x1404f1e84,struct.pack('<i',s['stage']));requests.clear();allocs.clear();fog.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x1400785c0,n.stack+0xf000,count=3000000)
        m.mem_write(0x1404ff26c,bytes(12));byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,501):
            paused=(80<=frame<=82)or frame==10000;m.mem_write(0x1404f27b9,bytes([paused]))
            if frame%180==0:m.mem_write(n.owner+0x68,b'\1')
            if frame in [30,250]:m.mem_write(n.owner+0xb8,struct.pack('<i',1));m.mem_write(n.owner,bytes(4));m.mem_write(n.owner+0xbc,b'\1')
            if frame in [200,400]:m.mem_write(n.owner+0xb8,bytes(4))
            fog.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140077bb0,n.stack+0xf000,count=3000000)
            for addr in [0x140078290,0x140078390]:
                sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(addr,n.stack+0xf000,count=3000000)
            if frame not in byFrame:continue
            c=byFrame[frame];assert m.reg_read(UC_X86_REG_EAX)==c['result'],(s['stage'],frame,'return');assert fog==c['events'],(s['stage'],frame,'fog',fog,c['events']);assert list(struct.unpack('<3f',m.mem_read(0x1404ff26c,12)))==c['direction'],(s['stage'],frame,'direction',list(struct.unpack('<3f',m.mem_read(0x1404ff26c,12))),c['direction'])
            assert hashlib.sha256(m.mem_read(rawBase,len(bytes.fromhex(s['bytes'])))).hexdigest()==c['fileSha'],(s['stage'],frame,'mutable file')
            actual=bytearray(m.mem_read(pool,s['primitives']*288))
            for index in range(s['primitives']):
                for field in [0xf0,0xf8]:
                    p=index*288+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
                p=index*288+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(actual).hexdigest()==c['poolSha'],(s['stage'],frame,'ANM pool');digest.update(actual)
            actual=bytearray(m.mem_read(n.owner,0x220))
            for field in [0xf0,0xf8]:
                p=0xd0+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=0xd0+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            for p in [0x28,0x1f0]:struct.pack_into('<Q',actual,p,struct.unpack_from('<Q',actual,p)[0]-rawBase)
            for p in [0x70,0x88,0xa8]:struct.pack_into('<Q',actual,p,1)
            wanted=bytes.fromhex(c['owner']);assert actual==wanted,(s['stage'],frame,'owner',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b]);digest.update(actual)
        print(json.dumps(dict(stage=s['stage'],frames=500,passed=True)),flush=True)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,stages=len(scenes),frames=500*len(scenes),checkpoints=sum(len(s['frames'])for s in scenes),objects=sum(s['objects']for s in scenes),primitives=sum(s['primitives']for s in scenes),instances=sum(s['instances']for s in scenes),instructions=sum(s['instructions']for s in scenes),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-std-spell-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
