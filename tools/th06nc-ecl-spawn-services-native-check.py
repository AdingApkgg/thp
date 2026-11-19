"""ECL 118/119/124 effect, scattered item and explicit item requests.

Original dispatch bodies execute. Effect/item creation is observed as service
requests, including the inline high-power point-item allocation boundary. Actual
entities and full game behavior are outside this proof.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[];
for(const opcode of [118,119,124])for(const count of [-1,0,1,3,8])for(const power of [0,127,128,65535])for(const practice of [false,true]){
 const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),rng=new NativeRng(0xbeef,99),environment={rng,playerPower:power,spellPractice:practice},operands=new EclOperands(enemy,environment),args=Buffer.alloc(12),events=[];[100.5,200.25,-2].forEach((x,i)=>v.setFloat32(0xb0+i*4,x,true));args.writeInt32LE(opcode===119?count:3);args.writeInt32LE(count,4);args.writeUInt32LE(0x89abcdef,8);const before=Buffer.from(enemy).toString('hex');
 applyEclCommand(enemy,{opcode,args},{operands,gameEnvironment:environment,spawnEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e}),spawnPointItem:e=>events.push({kind:'point',...e})});cases.push({opcode,args:args.toString('hex'),power,practice,before,after:Buffer.from(enemy).toString('hex'),events,rng:{seed:rng.seed,count:rng.count}});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140027fbb:
            events.append(dict(kind='point',position=list(struct.unpack('<3f',m.mem_read(sp+0x58,12)))));m.reg_write(UC_X86_REG_RBX,0x9630);m.reg_write(UC_X86_REG_RIP,0x1400280fa);return
        if a not in [0x14002b0d0,0x1400426e0]:return
        pos=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
        if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=pos,count=struct.unpack('<i',struct.pack('<I',m.reg_read(UC_X86_REG_R9D)))[0],color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0]))
        else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=pos,critical=bool(m.reg_read(UC_X86_REG_R9D))))
        m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        raw=bytes.fromhex(c['args']);m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets,struct.pack('<ihH4B',0,c['opcode'],12+len(raw),0,255,0,0)+raw);m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f1e88,struct.pack('<H',c['power']));m.mem_write(0x1404f27b5,bytes([c['practice']]));sp=n.stack+0x8000;m.mem_write(sp+0x48,struct.pack('<Q',n.assets))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R10,0x140000000),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1),(UC_X86_REG_RBX,0x9630),(UC_X86_REG_XMM14,int.from_bytes(struct.pack('<f',2**-32),'little'))]:m.reg_write(reg,value)
        start={118:0x140027e43,119:0x140027e62,124:0x1400284b7}[c['opcode']];events.clear();m.emu_start(start,0x140025d7d,count=100000);assert events==c['events'],(index,c['opcode'],events,c['events']);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],(index,'enemy');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual+json.dumps(events).encode())
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/ecl-command.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-spawn-services-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
