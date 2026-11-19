"""Real STD layer drawing against native 78cb0, including native matrix math.

Compare ordered world/screen ANM calls, complete mutable ANM pool, and texture
factor requests. Controlled view/projection/viewport isolate instance traversal,
Y-only corner culling and billboard mutation. GPU transport is observed.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/std.mjs','shared/th06nc/std-state.mjs','shared/th06nc/std-update.mjs','shared/th06nc/matrix.mjs','shared/th06nc/std-draw.mjs','shared/th06nc/std-camera.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{createStdCamera}from'./shared/th06nc/std-camera.mjs';import{createHash}from'node:crypto';import{drawStdLayer}from'./shared/th06nc/std-draw.mjs';import{advanceStd}from'./shared/th06nc/std-update.mjs';import{readFileSync}from'node:fs';import{readStd}from'./shared/th06nc/std.mjs';import{initializeStd,stdAssetPlan}from'./shared/th06nc/std-state.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');for(let stage=1;stage<=7;stage++){const ref=stdAssetPlan(stage),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const program=readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),state=initializeStd(program,{anmBank:bank});const draws=[];let previous=0;for(const frame of [0,1,60,180,600,1800,4200,9000]){for(let f=previous;f<frame;f++){if(f%180===0)state.v.setUint8(0x68,1);advanceStd(state);}previous=frame;for(const mode of ['ortho','perspective','native'])for(const billboard of [false,true]){if(billboard)for(let i=0;i<state.vms.length;i+=5)state.vms[i].v.setInt16(0x88,2,true);const realCamera=createStdCamera({direction:state.direction??[0,0,1]}),view=mode==='native'?realCamera.view:new Float32Array([1,0,0,0,0,.8,0,0,0,0,.9,0,0,0,600,1]),projection=mode==='native'?realCamera.projection:mode==='ortho'?new Float32Array([2/384,0,0,0,0,2/448,0,0,0,0,1/2000,0,0,0,0,1]):new Float32Array([1.8,0,0,0,0,2,0,0,0,0,1.001,1,0,0,-1.001,0]),viewport=mode==='native'?{x:32,y:16,width:384,height:448,minZ:0,maxZ:1}:{x:72,y:36,width:864,height:1008,minZ:.1,maxZ:.95},calls=[],factors=[];for(let layer=0;layer<4;layer++)drawStdLayer(state,layer,(vm,r)=>calls.push({space:r.space,index:r.index,sha256:sha(vm.state),debug:hex(vm.state)}),{view,projection,viewport,setTextureFactor:r=>factors.push(r)});draws.push({frame,mode,billboard,view:[...view],projection:[...projection],viewport,calls,factors,poolSha:sha(state.storage)});}}scenes.push({stage,ref,draws,objects:program.objectCount,primitives:program.primitiveCount,instances:program.instances.length,instructions:program.instructions.length,bytes:hex(state.bytes),storage:hex(state.storage),owner:hex(state.owner)});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;rawBase=n.assets+0x100000;table=n.owner+0x400;pool=n.owner+0x1000;requests=[];allocs=[];fog=[];calls=[];factors=[];drawCount=0;digest=hashlib.sha256()
    def string(ptr):return bytes(m.mem_read(ptr,128)).split(b'\0')[0].decode()
    def hook(m,a,size,u):
        if a in [0x140004dc0,0x140004310]:
            ptr=m.reg_read(UC_X86_REG_RDX);actual=bytearray(m.mem_read(ptr,288));normalizeVm(actual);calls.append(dict(space='world'if a==0x140004dc0 else'screen',index=(ptr-pool)//288,sha256=hashlib.sha256(actual).hexdigest(),debug=actual.hex()))
        elif a==0x1400974e0:factors.append(dict(stage=m.reg_read(UC_X86_REG_ECX),operation=m.reg_read(UC_X86_REG_EDX),color=m.reg_read(UC_X86_REG_R8D)))
        elif a==0x1402bcf20:pass
        elif a==0x1400020b0:requests.append(dict(kind='anm',file=string(m.reg_read(UC_X86_REG_R8)),slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_EAX,0)
        elif a==0x1400387a0:requests.append(dict(kind='std',file=string(m.reg_read(UC_X86_REG_RCX))));m.reg_write(UC_X86_REG_RAX,rawBase)
        elif a==0x1402bd4a0:
            size=m.reg_read(UC_X86_REG_RCX);ptr=table if not allocs else pool;allocs.append(size);m.mem_write(ptr,bytes(size));m.reg_write(UC_X86_REG_RAX,ptr)
        elif a==0x1400969c0:fog.append(dict(kind='color',rgb=[m.reg_read(r)for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_R8D]]))
        elif a==0x140096b00:fog.append(dict(kind='range',values=[struct.unpack('<f',m.reg_read(r).to_bytes(16,'little')[:4])[0]for r in [UC_X86_REG_XMM0,UC_X86_REG_XMM1]]))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140004dc0,0x140004310,0x1400974e0,0x1402bcf20,0x1400020b0,0x1400387a0,0x1402bd4a0,0x1400969c0,0x140096b00]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def normalizeVm(actual,offset=0):
        for field in [0xf0,0xf8]:
            p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
        p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
        if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
    def run(addr):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(addr,n.stack+0xf000,count=3000000)
    for s in scenes:
        n.load_title([s['ref']]);m.mem_write(rawBase,(ROOT/f"runtimes/th06nc/artifacts/scripts/th06ST.dat/stage{s['stage']}.std").read_bytes());m.mem_write(n.owner,bytes(0x220));m.mem_write(0x1404f1e84,struct.pack('<i',s['stage']));requests.clear();allocs.clear();fog.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x1400785c0,n.stack+0xf000,count=3000000)
        previous=0;m.mem_write(0x1404f27b9,b'\0')
        for d in s['draws']:
            for frame in range(previous,d['frame']):
                if frame%180==0:m.mem_write(n.owner+0x68,b'\1')
                run(0x140077bb0)
            previous=d['frame']
            if d['billboard']:
                for i in range(0,s['primitives'],5):m.mem_write(pool+i*288+0x88,struct.pack('<h',2))
            m.mem_write(0x140c21d18,struct.pack('<16f',*d['view']));m.mem_write(0x140c21d58,struct.pack('<16f',*d['projection']));vp=d['viewport'];m.mem_write(0x140c21e24,struct.pack('<4I2f',vp['x'],vp['y'],vp['width'],vp['height'],vp['minZ'],vp['maxZ']));calls.clear();factors.clear()
            for layer in range(4):m.reg_write(UC_X86_REG_EDX,layer);run(0x140078cb0)
            assert factors==d['factors'],(s['stage'],d['frame'],'texture factors',factors,d['factors'])
            assert calls==d['calls'],(s['stage'],d['frame'],d['mode'],d['billboard'],'draw calls',len(calls),len(d['calls']),next(((i,a['index'],[(hex(p),x,y)for p,(x,y)in enumerate(zip(bytes.fromhex(a['debug']),bytes.fromhex(b['debug'])))if x!=y])for i,(a,b)in enumerate(zip(calls,d['calls']))if a!=b),None))
            actual=bytearray(m.mem_read(pool,s['primitives']*288))
            for i in range(s['primitives']):normalizeVm(actual,i*288)
            assert hashlib.sha256(actual).hexdigest()==d['poolSha'],(s['stage'],d['frame'],d['mode'],d['billboard'],'ANM pool');digest.update(actual);drawCount+=len(calls)
        print(json.dumps(dict(stage=s['stage'],cases=len(s['draws']),passed=True)),flush=True)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,stages=len(scenes),cases=sum(len(s['draws'])for s in scenes),drawCalls=drawCount,objects=sum(s['objects']for s in scenes),primitives=sum(s['primitives']for s in scenes),instances=sum(s['instances']for s in scenes),instructions=sum(s['instructions']for s in scenes),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-std-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
