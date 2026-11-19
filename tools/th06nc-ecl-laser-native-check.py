"""ECL 85/86 laser descriptors and saved handles using original dispatch bodies.

Original operand helpers execute; the laser constructor is an observed service.
Full enemy, operand scratch and RNG compared; actual lasers separately checked.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{configureEclLaser}from'./shared/th06nc/ecl-laser-config.mjs';const unique=new Map(),cases=[];
for(const file of JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.ecl')))for(const sub of readEcl(readFileSync(file.path)).subroutines)for(const ins of sub.instructions)if([85,86].includes(ins.opcode))unique.set(ins.opcode+':'+Buffer.from(ins.args).toString('hex'),ins);
for(const opcode of [85,86])for(const value of [1.25,-10015,-10100]){const args=Buffer.alloc(52);for(const p of [4,8,12,16,20])args.writeFloatLE(value,p);unique.set(opcode+':synthetic:'+value,{opcode,args});}
for(const ins of unique.values())for(const missing of [false,true]){
 const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);enemy.fill(0,0xf80,0x1080);v.setInt32(0xbd8,1,true);const environment={rng:new NativeRng(0xbeef,99),playerPosition:[192,400,0],atan2:()=>0.875},operands=new EclOperands(enemy,environment),before=Buffer.from(enemy).toString('hex'),events=[],laserBindings=new Map();configureEclLaser(enemy,ins,{operands,laserBindings,spawnLaser:d=>{events.push(Buffer.from(d).toString('hex'));return missing?null:{pointer:1n};}});cases.push({opcode:ins.opcode,args:Buffer.from(ins.args).toString('hex'),missing,before,after:Buffer.from(enemy).toString('hex'),events,scratch:Buffer.from(operands.scratch).toString('hex'),rng:{seed:environment.rng.seed,count:environment.rng.count}});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];current=None;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x1400105e0:events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),68)).hex());m.reg_write(UC_X86_REG_RAX,0 if current['missing']else n.manager)
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x1400105e0,0x1402be065]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    for index,c in enumerate(cases):
        current=c;raw=bytes.fromhex(c['args']);m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets,struct.pack('<ihH4B',0,c['opcode'],12+len(raw),0,255,0,0)+raw);m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0))
        for address in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]:m.mem_write(address,bytes(4))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1)]:m.reg_write(reg,value)
        events.clear();m.emu_start(0x140026aa4,0x140025d7d,count=100000);assert events==c['events'],(index,'descriptor');actual=bytearray(m.mem_read(n.owner,0x1100));ptr=struct.unpack_from('<Q',actual,0xf88)[0];struct.pack_into('<Q',actual,0xf88,1 if ptr else 0);assert actual.hex()==c['after'],(index,'enemy');scratch=b''.join(bytes(m.mem_read(a,4))for a in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]);assert scratch.hex()==c['scratch'],(index,'scratch');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual+scratch)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/ecl-laser-config.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-laser-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
