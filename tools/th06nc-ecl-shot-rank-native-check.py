"""ECL shot rank adjustments and repeat-fire intervals, original x64 bodies.

Compares complete enemy bytes and shared RNG/sound/operand scratch. atan2/sine/cosine/fmod thunks
use shared supplied results; native CRT precision is excluded. Bullet service calls are observed; projectiles, interpreter, enemy frame and GPU excluded.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{applyEclCommand,supportedEclCommands}from'./shared/th06nc/ecl-command.mjs';
const unique=new Map();for(const file of JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.ecl')))for(const sub of readEcl(readFileSync(file.path)).subroutines)for(const ins of sub.instructions)if([67,68,69,70,71,72,73,74,75,76,77,201].includes(ins.opcode))unique.set(ins.opcode+':'+Buffer.from(ins.args).toString('hex'),ins);
for(const opcode of [67,68,69,70,71,72,73,74,75,76,77,201]){const args=Buffer.alloc(64);if([109,129].includes(opcode)){args.writeInt32LE(1,0);args.writeInt32LE(1,4);}else if([4,5].includes(opcode)){args.writeInt32LE(-10001,0);args.writeInt32LE(42,4);}else if([6,7,8,9].includes(opcode)){args.writeInt32LE(opcode<8?-10001:-10005,0);args.writeInt32LE(opcode<8?12:0x41400000,4);args.writeInt32LE(opcode<8?3:0x40400000,8);}else if([13,14,15,16,17,20,21,22,23,24].includes(opcode)){args.writeInt32LE(-10001,0);args.writeInt32LE(12,4);args.writeInt32LE(3,8);}else args.writeInt32LE(1,0);unique.set('synthetic:'+opcode,{opcode,args});}
const cases=[];for(const ins of [...unique.values()].filter((ins,index,all)=>all.slice(0,index).filter(x=>x.opcode===ins.opcode).length<12))for(const initialFlags of [0,255])for(const rank of [0,8,16,24,32]){
const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);for(const p of [0xbc,0xbd,0xbe])v.setUint8(p,initialFlags);for(const [p,x]of [[0x28,0],[0x2c,0],[0x30,384],[0x34,448]])v.setFloat32(p,x,true);
const environment={difficulty:3,rank,playerPosition:[32,-16,8],character:1,shot:0,rng:new NativeRng(0xbeef,99),atan2:()=>0.875},operands=new EclOperands(enemy,environment),before=Buffer.from(enemy).toString('hex'),events=[],initialSound=initialFlags?[12,-1,-1]:[-1,-1,-1],result=applyEclCommand(enemy,ins,{operands,sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,fireBullets:(e,s)=>events.push(Buffer.from(s).toString('hex')),soundSlots:[...initialSound]});cases.push({rank,opcode:ins.opcode,args:Buffer.from(ins.args).toString('hex'),before,initialSound,events,result,after:Buffer.from(enemy).toString('hex'),scratch:Buffer.from(operands.scratch).toString('hex'),rng:{seed:environment.rng.seed,count:environment.rng.count}});}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();events=[]
    def hook(m,a,size,u):
        if a==0x14000f870:
            events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex());sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);return
        if a in [0x1402be071,0x1402be07d]:
            value=0.75 if a==0x1402be071 else 0.25;m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);return
        if a==0x1402be077:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];y=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM1).to_bytes(16,'little')[:4])[0];value=math.fmod(x,y);m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);return
        if a!=0x1402be065:return
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        events.clear();m.mem_write(0x1404ff27c,struct.pack('<i',c['rank']));raw=bytes.fromhex(c['args']);m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets,struct.pack('<ihH4B',0,c['opcode'],12+len(raw),0,255,0,0)+raw);m.mem_write(0x1404f27c0,struct.pack('<i',3));m.mem_write(0x1404f1e80,b'\1\0');m.mem_write(0x140506ad0,struct.pack('<3f',32,-16,8));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140509670,struct.pack('<3i',*c['initialSound']));m.mem_write(0x140509694,b'\0');m.mem_write(0x140a6ebec,b'\0')
        for address in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]:m.mem_write(address,bytes(4))
        sp=n.stack+0x8000;m.mem_write(sp+0x48,struct.pack('<Q',n.assets))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R10,0x140000000),(UC_X86_REG_R12,0),(UC_X86_REG_XMM8,0),*[(r,int.from_bytes(struct.pack('<f',x),'little'))for r,x in [(UC_X86_REG_XMM9,3.1415927410125732),(UC_X86_REG_XMM10,6.2831854820251465),(UC_X86_REG_XMM11,-3.1415927410125732),(UC_X86_REG_XMM12,-6.2831854820251465)]],(UC_X86_REG_XMM13,int.from_bytes(struct.pack('<f',1.5707963705062866),'little')),(UC_X86_REG_XMM14,int.from_bytes(struct.pack('<f',2**-32),'little')),(UC_X86_REG_R15,1),(UC_X86_REG_RBX,0x9630),(UC_X86_REG_R11,0x6553)]:m.reg_write(reg,value)
        if c['opcode']==0:pass
        else:
            idx=m.mem_read(0x140028f5c+c['opcode']-1,1)[0];dst=struct.unpack('<I',m.mem_read(0x140028d78+idx*4,4))[0];m.emu_start(0x140000000+dst,0x140025d7d,count=100000)
        assert events==c['events'],(index,c['opcode'],events,c['events']);actual=bytes(m.mem_read(n.owner,0x1100));wanted=bytes.fromhex(c['after']);diff=[hex(i)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,c['opcode'],c['args'],diff)
        scratch=b''.join(bytes(m.mem_read(a,4))for a in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]);assert scratch.hex()==c['scratch'],(index,c['opcode'],scratch.hex(),c['scratch'])
        count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],index
        result=dict(soundSlots=list(struct.unpack('<3i',m.mem_read(0x140509670,12))),bossLifeDirty=bool(m.mem_read(0x140a6ebec,1)[0]));assert result==c['result'],(index,c['opcode'],result,c['result']);digest.update(actual+scratch)
    report=dict(scope=__doc__,cases=len(cases),opcodes=sorted(set(c['opcode']for c in cases)),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-command.mjs','shared/th06nc/ecl-operands.mjs','shared/th06nc/rng.mjs','shared/th06nc/ecl-shot-config.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-shot-rank-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
