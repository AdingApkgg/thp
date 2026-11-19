"""Enemy linked effect attachment, following, strength/angle updates and release.

Original opcode 102 and manager blocks execute; effect creation is a controlled
state-handle service. Actual effect callbacks, rendering and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{attachEnemyEffect,advanceEnemyEffects,releaseEnemyEffects}from'./shared/th06nc/enemy-linked-effects.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
const make=(count,angle,strength,target)=>{const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),effects=Array.from({length:8},(_,i)=>{const bytes=new Uint8Array(0x198),v=new DataView(bytes.buffer);v.setFloat32(0x2c,angle,true);v.setFloat32(0x184,strength,true);return{bytes,v,pointer:BigInt(i+1)};}),linkedEffects=new Map(effects.map(e=>[e.pointer,e]));v.setInt32(0x1090,count,true);v.setFloat32(0x268,target,true);[100.5,200.25,-2].forEach((x,i)=>v.setFloat32(0xb0+i*4,x,true));for(let i=0;i<count;i++)if(i!==1)v.setBigUint64(0xbe8+i*8,BigInt(i+1),true);return{enemy,v,linkedEffects,effects};};
const save=e=>({enemy:hex(e.enemy),effects:e.effects.map(f=>hex(f.bytes))});
for(let color=0;color<28;color++)for(const count of [0,3,7]){
 const entry=make(count,0,0,0),args=Buffer.alloc(20);args.writeInt32LE(color);[1.25,2.5,3.75,4.5].forEach((x,i)=>args.writeFloatLE(x,4+i*4));const before=save(entry),events=[];
 attachEnemyEffect(entry.enemy,args,{linkedEffects:entry.linkedEffects,spawnEffect:request=>{events.push(request);return entry.effects[count];}});cases.push({kind:'attach',before,after:save(entry),args:hex(args),events,count});
}
for(const count of [0,1,3])for(const angle of [-1000,-4,-Math.PI,0,Math.PI,4,1000])for(const strength of [0,0.3,5])for(const target of [-1,0,5]){
 const entry=make(count,angle,strength,target),before=save(entry);advanceEnemyEffects(entry);cases.push({kind:'advance',before,after:save(entry)});
}
for(const count of [-1,0,1,3,8]){const entry=make(count,0,1,2),before=save(entry);releaseEnemyEffects(entry);cases.push({kind:'release',before,after:save(entry)});}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;fxbase=n.manager+0x10000;events=[];current=None;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a!=0x14002b0d0:return
        sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(type=m.reg_read(UC_X86_REG_EDX),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12))),count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0]));m.reg_write(UC_X86_REG_RAX,fxbase+current['count']*0x198);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        current=c;state=bytearray.fromhex(c['before']['enemy'])
        for i in range(8):
            p=0xbe8+i*8;ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,fxbase+(ptr-1)*0x198)
        m.mem_write(n.owner,bytes(state))
        for i,raw in enumerate(c['before']['effects']):m.mem_write(fxbase+i*0x198,bytes.fromhex(raw))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,n.owner),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R14,0),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1),(UC_X86_REG_R10,0x140000000)]:m.reg_write(reg,value)
        events.clear()
        if c['kind']=='attach':
            m.mem_write(n.assets,bytes(12)+bytes.fromhex(c['args']));m.reg_write(UC_X86_REG_R14,n.assets);m.reg_write(UC_X86_REG_RSI,n.assets+12);m.emu_start(0x140027249,0x140025d7d,count=10000);assert events==c['events'],(index,'events',events,c['events'])
        elif c['kind']=='advance':
            for reg,value in [(UC_X86_REG_XMM11,0.3),(UC_X86_REG_XMM12,0.03141592815518379),(UC_X86_REG_XMM6,3.1415927410125732),(UC_X86_REG_XMM8,-6.2831854820251465),(UC_X86_REG_XMM7,-3.1415927410125732),(UC_X86_REG_XMM9,6.2831854820251465)]:m.reg_write(reg,int.from_bytes(struct.pack('<f',value),'little'))
            m.emu_start(0x140038095,0x14003815c,count=10000)
        else:m.emu_start(0x140037c8d,0x140037cc7,count=10000)
        actual=bytearray(m.mem_read(n.owner,0x10b0))
        for i in range(8):
            p=0xbe8+i*8;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-fxbase)//0x198+1)
        assert actual.hex()==c['after']['enemy'],(index,'enemy');digest.update(actual)
        for i,raw in enumerate(c['after']['effects']):
            actual=bytes(m.mem_read(fxbase+i*0x198,0x198));wanted=bytes.fromhex(raw);diff=[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,c['kind'],i,diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/enemy-linked-effects.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-linked-effects-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
