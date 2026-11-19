"""ECL frame tail: repeat-shot request, direction ANM, callback and clock commit.

Original ANM setter/tick executes. Bullet manager and custom callback are supplied
observable services; actual projectiles, manager motion and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{rebindAnm}from'./shared/th06nc/anm-rebind.mjs';import{finishEclEnemyFrame}from'./shared/th06nc/ecl-enemy-tail.mjs';
const ref={archive:'th06ST.dat',file:'stg1enm.anm',slot:8,base:256},resource=readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stg1enm.anm')),bank=new AnmBank();bank.load(resource,256,{slot:8});const cases=[];
for(const life of [0,100])for(const interval of [0,2,3])for(const clock of [0,1,2])for(const automatic of [false,true])for(const velocity of [-1,0,1])for(const previous of [255,0,1,2])for(const custom of [false,true]){
const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);for(const p of [0xf0,0xf8,0x100])v.setBigUint64(0x108+p,0n,true);
const vm=rebindAnm(bank,256,enemy.subarray(0x108,0x228));v.setInt32(0x234,life,true);v.setInt32(0xf68,interval,true);v.setInt32(0x10a4,clock,true);v.setInt16(0xf6c,automatic?1:-1,true);v.setInt16(0xf6e,2,true);v.setInt16(0x109c,0,true);v.setInt16(0x2bc,3,true);v.setInt16(0x2be,4,true);v.setFloat32(0x1084,velocity,true);v.setUint8(0xf7c,previous);v.setBigUint64(0x98,custom?0x1234n:0n,true);v.setInt32(0x44,19,true);v.setBigUint64(0x88,0x40n,true);
const before=Buffer.from(enemy).toString('hex'),events=[];finishEclEnemyFrame(enemy,0x80,{anmBank:bank,enemyAnms:new Map([[0x108,vm]]),fireBullets:(e,shot)=>events.push({kind:'shot',descriptor:Buffer.from(shot).toString('hex')}),enemyCallback:(e,arg)=>{events.push({kind:'callback',arg});v.setInt32(0xa0,v.getInt32(0xa0,true)+17,true);}});cases.push({before,after:Buffer.from(enemy).toString('hex'),events});}
console.log(JSON.stringify({ref,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;events=[];digest=hashlib.sha256();callback=n.vm+0xf000
    def hook(m,a,size,u):
        if a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()))
        elif a==callback:
            events.append(dict(kind='callback',arg=m.reg_read(UC_X86_REG_RDX)));value=struct.unpack('<i',m.mem_read(n.owner+0xa0,4))[0];m.mem_write(n.owner+0xa0,struct.pack('<i',value+17))
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(data['cases']):
        state=bytearray.fromhex(c['before']);custom=struct.unpack_from('<Q',state,0x98)[0]
        if custom:struct.pack_into('<Q',state,0x98,callback)
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',state,0x108+p)[0]
            if ptr:struct.pack_into('<Q',state,0x108+p,n.assets+ptr)
        ptr=struct.unpack_from('<Q',state,0x208)[0]
        if ptr:struct.pack_into('<Q',state,0x208,n.manager+0x608+(ptr-1)*64)
        m.mem_write(n.owner,bytes(state));events.clear()
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1),(UC_X86_REG_R14,0x80),(UC_X86_REG_XMM8,0)]:m.reg_write(reg,value)
        m.emu_start(0x140028a7d,0x140028d13,count=100000);assert events==c['events'],(index,events,c['events'])
        actual=bytearray(m.mem_read(n.owner,0x1100))
        if custom:struct.pack_into('<Q',actual,0x98,custom)
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',actual,0x108+p)[0]
            if ptr:struct.pack_into('<Q',actual,0x108+p,ptr-n.assets)
        ptr=struct.unpack_from('<Q',actual,0x208)[0]
        if ptr:struct.pack_into('<Q',actual,0x208,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-enemy-tail.mjs','shared/th06nc/anm-rebind.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-enemy-tail-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
