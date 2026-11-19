"""Enemy ANM update and draw bridges, actual ANM VM and original owner draw.

Observes low-level draw calls without GPU execution. 3D ANMs, rendering pixels,
full manager lifecycle, collision and gameplay are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{rebindAnm}from'./shared/th06nc/anm-rebind.mjs';import{advanceEnemyAnimations}from'./shared/th06nc/enemy-animation.mjs';import{drawEnemyAnimations}from'./shared/th06nc/enemy-draw.mjs';
const ref={archive:'th06ST.dat',file:'stg1enm.anm',slot:8,base:256},resource=readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stg1enm.anm')),bank=new AnmBank();bank.load(resource,256,{slot:8});
const make=()=>{const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),enemyAnms=new Map();for(const [i,offset]of [0x108,...Array.from({length:8},(_,i)=>0x2d8+i*288)].entries()){const vm=rebindAnm(bank,256+(i%8),enemy.subarray(offset,offset+288));enemyAnms.set(offset,vm);}v.setUint8(0xbc,128);v.setFloat32(0xb0,123.5,true);v.setFloat32(0xb4,234.25,true);v.setUint32(0xf74,0x80ffffff,true);return {enemy,v,enemyAnms};},animationCases=[],drawCases=[];
for(const ticks of [1,2,4,30,120]){const entry=make(),before=Buffer.from(entry.enemy).toString('hex');for(let i=0;i<ticks;i++)advanceEnemyAnimations(entry);animationCases.push({ticks,before,after:Buffer.from(entry.enemy).toString('hex')});}
for(const flag of [0,2,8,10])for(const angle of [0,0.75])for(const visible of [false,true]){
const entry=make();entry.v.setUint8(0xbe,flag);entry.v.setFloat32(0x22c,angle,true);for(const [offset,vm]of entry.enemyAnms){vm.v.setFloat32(0x18,0.25,true);vm.v.setFloat32(0x1c,-0.5,true);if(offset!==0x108)vm.v.setUint16(0x88,offset%576?1:0,true);if(!visible)vm.v.setUint32(0xec,0,true);}const before=Buffer.from(entry.enemy).toString('hex'),calls=[];drawEnemyAnimations(entry,(vm,options)=>calls.push({offset:[...entry.enemyAnms].find(([p,v])=>v===vm)[0],snap:options.snap,position:Buffer.from(vm.state.slice(0xc8,0xd4)).toString('hex'),rotation:vm.v.getUint32(0xa4,true)}),{worldOffset:[32,16]});drawCases.push({before,after:Buffer.from(entry.enemy).toString('hex'),calls});}
console.log(JSON.stringify({ref,animationCases,drawCases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;owner=0x140aa1e90;enemy=owner+8;offsets=[0x108,*[0x2d8+i*288 for i in range(8)]];digest=hashlib.sha256();calls=[]
    def hook(m,a,size,u):
        if a==0x1400036c0:
            ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(offset=ptr-enemy,snap=bool(m.reg_read(UC_X86_REG_R8)&255),position=bytes(m.mem_read(ptr+0xc8,12)).hex(),rotation=struct.unpack('<I',m.mem_read(ptr+0xa4,4))[0]))
        elif a not in [0x14007af40,0x14007b120]:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    def pointers(state,toNative):
        state=bytearray(state)
        for offset in offsets:
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,offset+p)[0]
                if ptr:struct.pack_into('<Q',state,offset+p,ptr+n.assets if toNative else ptr-n.assets)
            ptr=struct.unpack_from('<Q',state,offset+0x100)[0]
            if ptr:struct.pack_into('<Q',state,offset+0x100,n.manager+0x608+(ptr-1)*64 if toNative else(ptr-n.manager-0x608)//64+1)
        return bytes(state)
    for index,c in enumerate(data['animationCases']):
        m.mem_write(enemy,pointers(bytes.fromhex(c['before']),True))
        for tick in range(c['ticks']):
            for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,enemy),(UC_X86_REG_R14,0),(UC_X86_REG_RDI,0xffffffffffffffff)]:m.reg_write(reg,value)
            m.emu_start(0x140037875,0x1400379e0,count=100000)
        actual=pointers(m.mem_read(enemy,0x10b0),False);wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,diff);digest.update(actual)
    for index,c in enumerate(data['drawCases']):
        m.mem_write(owner,bytes(0x10d1e0));m.mem_write(enemy,pointers(bytes.fromhex(c['before']),True));m.mem_write(0x1404f1e70,struct.pack('<2f',32,16));calls.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(0x140038290,n.stack+0xf000,count=100000)
        assert calls==c['calls'],(index,calls,c['calls']);actual=pointers(m.mem_read(enemy,0x10b0),False);wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,diff);digest.update(actual)
    report=dict(scope=__doc__,animationCases=len(data['animationCases']),drawCases=len(data['drawCases']),drawCalls=sum(len(c['calls'])for c in data['drawCases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/enemy-animation.mjs','shared/th06nc/enemy-draw.mjs','shared/th06nc/anm-rebind.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-animation-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
