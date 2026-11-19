"""ECL 95 child-spawn requests and ECL 96 whole-pool clear dispatch.

Native float operand resolution, inherited context and exact request fields;
child allocation is observed. Clear compares all 256 actors, including inactive,
boss, collidable and direct death-subroutine branches. GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-command.mjs','shared/th06nc/enemy-world.mjs','shared/th06nc/enemy-clear.mjs','shared/th06nc/ecl-operands.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EnemyWorld}from'./shared/th06nc/enemy-world.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';const hex=b=>Buffer.from(b).toString('hex'),spawns=[],clears=[];
for(const life of [0,1,32767,65535])for(const item of [0,2,65535])for(const indirect of [false,true]){const enemy=Uint8Array.from({length:0x10b0},(_,i)=>i&255),v=new DataView(enemy.buffer);for(let k=0;k<3;k++)v.setFloat32(0xb0+k*4,[100.5,200.25,-2][k],true);const args=new Uint8Array(24),a=new DataView(args.buffer);a.setInt32(0,3,true);for(let k=0;k<3;k++)a.setFloat32(4+k*4,indirect?-10015-k:[32,-16,8][k],true);a.setUint16(16,life,true);a.setUint16(18,item,true);a.setInt32(20,-123,true);const before=hex(enemy),events=[],operands=new EclOperands(enemy);applyEclCommand(enemy,{opcode:95,args},{operands,spawnEnemy:r=>events.push({...r,context:hex(r.context)})});spawns.push({args:hex(args),before,after:hex(enemy),events});}
const program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata3.ecl'));for(const variant of [0,1,2,3]){const world=new EnemyWorld(program,{anmBank:new AnmBank()}),pool=world.pool;for(let slot=0;slot<256;slot++){const enemy=pool.storage.subarray(slot*0x10b0,(slot+1)*0x10b0),v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);enemy.fill((slot+variant)&255);v.setUint8(0xbc,slot%2?128:0);v.setUint8(0xbd,(slot>>1)&15);v.setInt32(0x234,123,true);v.setInt32(0xbe0,(slot+variant)%3===0?-1:(slot+variant)%4,true);v.setBigUint64(0x88,0n,true);pool.entries[slot]={v,dispatch:{pointer:p=>v.setBigUint64(0x88,BigInt(p),true)}};}const before=hex(pool.storage);applyEclCommand(new Uint8Array(0x10b0),{opcode:96,args:new Uint8Array()},world.services);clears.push({before,after:hex(pool.storage)});}console.log(JSON.stringify({spawns,clears,subOffsets:program.subroutines.map(s=>s.offset)}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP);events.append(dict(sub=m.reg_read(UC_X86_REG_EDX),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12))),life=m.reg_read(UC_X86_REG_R9D),item=struct.unpack('<H',m.mem_read(sp+0x28,2))[0],score=struct.unpack('<i',m.mem_read(sp+0x30,4))[0],context=bytes(m.mem_read(struct.unpack('<Q',m.mem_read(sp+0x38,8))[0],96)).hex()));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1400360d0,end=0x1400360d0)
    for index,c in enumerate(data['spawns']):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets,bytes.fromhex(c['args']));sp=n.stack+0x8000
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets),(UC_X86_REG_R13,n.owner+0x40)]:m.reg_write(reg,value)
        events.clear();m.emu_start(0x1400284f2,0x140025d7d,count=100000);assert events==c['events'],(index,events,c['events']);assert bytes(m.mem_read(n.owner,0x10b0)).hex()==c['after'];digest.update(json.dumps(events).encode())
    poolBase=0x140aa1e98;programBase=n.assets+0x100000
    for i,p in enumerate(data['subOffsets']):m.mem_write(n.vm+i*8,struct.pack('<Q',programBase+p))
    m.mem_write(0x140a6eb80,struct.pack('<Q',n.vm))
    for index,c in enumerate(data['clears']):
        m.mem_write(poolBase,bytes.fromhex(c['before']));m.reg_write(UC_X86_REG_R12,0);m.emu_start(0x140028574,0x140025d7d,count=100000);actual=bytearray(m.mem_read(poolBase,256*0x10b0))
        for slot in range(256):
            p=slot*0x10b0+0x88;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,ptr-programBase)
        wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,'clear',[(hex(p//0x10b0),hex(p%0x10b0),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,spawnCases=len(data['spawns']),clearCases=len(data['clears']),actorsCompared=256*len(data['clears']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-enemy-services-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
