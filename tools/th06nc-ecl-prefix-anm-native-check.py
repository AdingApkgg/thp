"""Script-phase prefixes with real stage enemy ANM resources and setter/tick.

Starts subroutines in a controlled enemy context. Stops before unsupported
instructions, root return, and enemy motion. No complete stage/gameplay claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{EclDispatch}from'./shared/th06nc/ecl-dispatch.mjs';import{supportedEclCommands}from'./shared/th06nc/ecl-command.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';
const supported=[...new Set([...supportedEclCommands,97,99,1,2,3,29,30,31,32,33,34,35,36,37,38,39,40,41,42])],can=op=>supported.includes(op)||(op>=136&&op<=199)||op<1||op>201,cases=[],files=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.ecl'));
const stagePlans=files.map((f,i)=>stageAssetPlan(i+1)),resources=new Map(stagePlans.flatMap(p=>p.enemyAnimations).map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+r.file))]));
for(const [fileIndex,file]of files.entries()){
const program=readEcl(readFileSync(file.path));
for(let sub=0;sub<program.subroutines.length;sub++)for(const difficulty of [0,1,2,3,4]){
 const anmBank=new AnmBank();loadStageEnemyBank(anmBank,resources,fileIndex+1);const enemyAnms=new Map(),bindings=()=>[...enemyAnms].map(([offset,vm])=>({offset,file:[...resources].find(([file,r])=>r===vm.resource)?.[0]}));
const shots=[];const enemy=new Uint8Array(0x1100),operands=new EclOperands(enemy,{difficulty,playerPosition:[192,400,0],character:0,shot:0,rng:new NativeRng(0xbeef,99),atan2:()=>0.875}),services={operands,anmBank,enemyAnms,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,fireBullets:(e,s)=>shots.push(Buffer.from(s).toString('hex')),soundSlots:[-1,-1,-1],bossLifeDirty:false},vm=new EclDispatch(program,enemy,services);vm.start(sub,{integer:7,floatBits:0x3fc00000});vm.v.setInt32(0x234,500,true);
 for(let frame=0;frame<4;frame++){
 shots.length=0;const before=Buffer.from(enemy).toString('hex'),rngBefore={seed:operands.environment.rng.seed,count:operands.environment.rng.count},scratchBefore=Buffer.from(operands.scratch).toString('hex'),soundBefore=[...services.soundSlots],bossBefore=services.bossLifeDirty,anmBefore=bindings();
 const result=vm.runDue({beforeInstruction:ins=>can(ins.opcode)&&!(ins.opcode===36&&vm.v.getInt32(0x240,true)===0)});
 if(result.executed)cases.push({fileIndex,sub,difficulty,frame,shots:[...shots],before,anmBefore,anmAfter:bindings(),rngBefore,scratchBefore,soundBefore,bossBefore,result,after:Buffer.from(enemy).toString('hex'),scratch:Buffer.from(operands.scratch).toString('hex'),rng:{seed:operands.environment.rng.seed,count:operands.environment.rng.count},soundAfter:[...services.soundSlots],bossAfter:services.bossLifeDirty});
 if(result.deleted||result.debugStopped)break;vm.commitAfterEnemyFrame(result);
 }
}
}
console.log(JSON.stringify({files,stagePlans,supported,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));cases=data['cases'];n=Native();m=n.m;digest=hashlib.sha256();executed=0;debugStopped=False;shotCalls=[];current=None;programBase=n.assets+0x100000;table=n.vm+0x8000
    can=lambda op:op in data['supported']or 136<=op<=199 or op<1 or op>201
    def hook(m,a,size,u):
        nonlocal executed,debugStopped
        if a==0x1400221b1:executed+=1
        elif a==0x140022190:
            ptr=m.reg_read(UC_X86_REG_R14);time=struct.unpack('<i',m.mem_read(ptr,4))[0];clock=struct.unpack('<i',m.mem_read(n.owner+0x44,4))[0];op=struct.unpack('<h',m.mem_read(ptr+4,2))[0]
            if time==clock and(not can(op)or(op==36 and struct.unpack('<i',m.mem_read(n.owner+0x240,4))[0]==0)):debugStopped=True;m.emu_stop()
        elif a==0x140028838:m.emu_stop()
        elif a==0x14000f870:
            shotCalls.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex());sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
        elif a in [0x1402be065,0x1402be077,0x1402be071,0x1402be07d]:
            if a in [0x1402be065,0x1402be071,0x1402be07d]:value={0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a]
            else:
                import math
                x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];y=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM1).to_bytes(16,'little')[:4])[0];value=math.fmod(x,y)
            m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        if current!=c['fileIndex']:
            current=c['fileIndex'];n.load_title(data['stagePlans'][current]['enemyAnimations']);program=open(data['files'][current]['path'],'rb').read();m.mem_write(programBase,program);count=struct.unpack_from('<H',program)[0]
            for i in range(count):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
            m.mem_write(0x140a6eb80,struct.pack('<Q',table))
        m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.mem_write(0x1404f1e80,bytes(2));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x140a6ec40,struct.pack('<IH',c['rngBefore']['count'],c['rngBefore']['seed']));m.mem_write(0x140509670,struct.pack('<3i',*c['soundBefore']));m.mem_write(0x140509694,b'\0');m.mem_write(0x140a6ebec,bytes([c['bossBefore']]))
        for j,address in enumerate([0x140a6eb98,0x140a6ebb8,0x140a6ebbc]):m.mem_write(address,bytes.fromhex(c['scratchBefore'])[j*4:j*4+4])
        state=bytearray.fromhex(c['before'])
        for p in [0x88,*[0xcb0+i*96 for i in range(8)]]:
            ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,programBase+ptr)
        for binding in c['anmBefore']:
            offset=binding['offset']
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,offset+p)[0]
                if ptr:struct.pack_into('<Q',state,offset+p,n.assetByFile[binding['file']]+ptr)
            ptr=struct.unpack_from('<Q',state,offset+0x100)[0]
            if ptr:struct.pack_into('<Q',state,offset+0x100,n.manager+0x608+(ptr-1)*64)
        m.mem_write(n.owner,bytes(state));sp=n.stack+0x8000
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R10,0x140000000),(UC_X86_REG_R12,0),(UC_X86_REG_XMM13,int.from_bytes(struct.pack('<f',1.5707963705062866),'little')),(UC_X86_REG_R15,1),(UC_X86_REG_RBX,0x9630),(UC_X86_REG_R11,0x6553),(UC_X86_REG_R9,0xffffffffffffffff),(UC_X86_REG_XMM14,int.from_bytes(struct.pack('<f',2**-32),'little'))]:m.reg_write(reg,value)
        shotCalls.clear();executed=0;debugStopped=False;m.emu_start(0x140022170,0x140028840,count=1000000)
        assert shotCalls==c['shots'],(index,shotCalls,c['shots']);assert executed==c['result']['executed'],(index,executed,c['result']);assert debugStopped==c['result'].get('debugStopped',False),index
        assert (m.reg_read(UC_X86_REG_RIP)==0x140028838)==c['result']['deleted'],index;assert m.reg_read(UC_X86_REG_R14)-programBase==c['result']['nextOffset'],(index,c['result'])
        actual=bytearray(m.mem_read(n.owner,0x1100))
        for p in [0x88,*[0xcb0+i*96 for i in range(8)]]:
            ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-programBase)
        for binding in c['anmAfter']:
            offset=binding['offset']
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,offset+p)[0]
                if ptr:struct.pack_into('<Q',actual,offset+p,ptr-n.assetByFile[binding['file']])
            ptr=struct.unpack_from('<Q',actual,offset+0x100)[0]
            if ptr:struct.pack_into('<Q',actual,offset+0x100,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,c['fileIndex'],c['sub'],c['frame'],diff)
        scratch=b''.join(bytes(m.mem_read(a,4))for a in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]);assert scratch.hex()==c['scratch'],(index,scratch.hex(),c['scratch'])
        count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],index;assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundAfter'],index;assert bool(m.mem_read(0x140a6ebec,1)[0])==c['bossAfter'],index;digest.update(actual+scratch)
    report=dict(scope=__doc__,cases=len(cases),commands=sum(c['result']['executed']for c in cases),subroutinesWithExecutedPrefix=len(set((c['fileIndex'],c['sub'])for c in cases)),files=[dict(name=f['name'],sha256=f['sha256'])for f in data['files']],stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-dispatch.mjs','shared/th06nc/ecl-command.mjs','shared/th06nc/ecl-operands.mjs','shared/th06nc/ecl-shot-config.mjs','shared/th06nc/rng.mjs','shared/th06nc/anm-rebind.mjs','shared/th06nc/stage-layout.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-prefix-anm-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
