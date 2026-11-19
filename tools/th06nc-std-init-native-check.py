"""STD loader initialization on all seven original backgrounds.

Compare mutable STD bytes, complete ANM pool and background owner with native
785c0. Asset loading, allocation and fog GPU calls are observed services. This
does not prove camera updates, culling, projection or final pixels.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/std.mjs','shared/th06nc/std-state.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{readStd}from'./shared/th06nc/std.mjs';import{initializeStd,stdAssetPlan}from'./shared/th06nc/std-state.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');for(let stage=1;stage<=7;stage++){const ref=stdAssetPlan(stage),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const program=readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),state=initializeStd(program,{anmBank:bank});scenes.push({stage,ref,objects:program.objectCount,primitives:program.primitiveCount,instances:program.instances.length,instructions:program.instructions.length,bytes:hex(state.bytes),storage:hex(state.storage),owner:hex(state.owner)});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;rawBase=n.assets+0x100000;table=n.owner+0x400;pool=n.owner+0x1000;requests=[];allocs=[];fog=[];digest=hashlib.sha256()
    def string(ptr):return bytes(m.mem_read(ptr,128)).split(b'\0')[0].decode()
    def hook(m,a,size,u):
        if a==0x1400020b0:requests.append(dict(kind='anm',file=string(m.reg_read(UC_X86_REG_R8)),slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_EAX,0)
        elif a==0x1400387a0:requests.append(dict(kind='std',file=string(m.reg_read(UC_X86_REG_RCX))));m.reg_write(UC_X86_REG_RAX,rawBase)
        elif a==0x1402bd4a0:
            size=m.reg_read(UC_X86_REG_RCX);ptr=table if not allocs else pool;allocs.append(size);m.mem_write(ptr,bytes(size));m.reg_write(UC_X86_REG_RAX,ptr)
        elif a==0x1400969c0:fog.append(dict(kind='color',rgb=[m.reg_read(r)for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_R8D]]))
        elif a==0x140096b00:fog.append(dict(kind='range',values=[struct.unpack('<f',m.reg_read(r).to_bytes(16,'little')[:4])[0]for r in [UC_X86_REG_XMM0,UC_X86_REG_XMM1]]))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400020b0,0x1400387a0,0x1402bd4a0,0x1400969c0,0x140096b00]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for s in scenes:
        n.load_title([s['ref']]);m.mem_write(rawBase,(ROOT/f"runtimes/th06nc/artifacts/scripts/th06ST.dat/stage{s['stage']}.std").read_bytes());m.mem_write(n.owner,bytes(0x220));m.mem_write(0x1404f1e84,struct.pack('<i',s['stage']));requests.clear();allocs.clear();fog.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x1400785c0,n.stack+0xf000,count=3000000)
        assert m.reg_read(UC_X86_REG_EAX)==0,(s['stage'],'return');assert requests==[dict(kind='anm',file='data/'+s['ref']['file'],slot=4,base=0x320),dict(kind='std',file=f"data/stage{s['stage']}.std")],requests;assert allocs==[s['objects']*8,s['primitives']*288],allocs;assert fog==[dict(kind='color',rgb=[0,0,0]),dict(kind='range',values=[200,500])],fog
        wantedFile=bytes.fromhex(s['bytes']);actualFile=bytes(m.mem_read(rawBase,len(wantedFile)));assert actualFile==wantedFile,(s['stage'],'mutated STD',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actualFile,wantedFile))if a!=b][:40])
        actual=bytearray(m.mem_read(pool,s['primitives']*288))
        for index in range(s['primitives']):
            for field in [0xf0,0xf8]:
                p=index*288+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
            p=index*288+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(s['storage']);assert actual==wanted,(s['stage'],'ANM pool',[(hex(i//288),hex(i%288),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:40]);digest.update(actual)
        actual=bytearray(m.mem_read(n.owner,0x220))
        for p in [0x28,0x1f0]:struct.pack_into('<Q',actual,p,struct.unpack_from('<Q',actual,p)[0]-rawBase)
        for p in [0x70,0x88,0xa8]:struct.pack_into('<Q',actual,p,1)
        wanted=bytes.fromhex(s['owner']);assert actual==wanted,(s['stage'],'owner',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b]);digest.update(actual)
        assert [struct.unpack('<Q',m.mem_read(table+i*8,8))[0]-rawBase for i in range(s['objects'])]==list(struct.unpack_from('<'+'I'*s['objects'],bytes.fromhex(s['bytes']),0x490))
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,stages=len(scenes),objects=sum(s['objects']for s in scenes),primitives=sum(s['primitives']for s in scenes),instances=sum(s['instances']for s in scenes),instructions=sum(s['instructions']for s in scenes),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-std-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
