"""Saved laser operations 88..92, original dispatch and operand helpers.

Compares full enemy/laser bytes and shared RNG. Aiming uses a supplied native
atan2 result; native CRT precision and full projectile simulation excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{controlEclLaser}from'./shared/th06nc/ecl-laser-control.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(const opcode of [88,89,90,91,92])for(const value of [1.25,-10015,-10100])for(const missing of [false,true])for(const active of [0,1,2])for(const mode of [0,1,2,3])for(const coincident of [false,true]){
 const enemy=new Uint8Array(0x10b0),laser=new Uint8Array(0x298),v=new DataView(enemy.buffer),l=new DataView(laser.buffer),rng=new NativeRng(0xbeef,99),environment={rng,playerPosition:[192,400,0],atan2:()=>0.875},operands=new EclOperands(enemy,environment),args=Buffer.alloc(16);args.writeInt32LE(1);for(const p of [4,8,12])args.writeFloatLE(value,p);[100.5,200.25,-2].forEach((x,i)=>v.setFloat32(0xb0+i*4,x,true));[coincident?192:100,coincident?400:200,0].forEach((x,i)=>l.setFloat32(0x278+i*4,x,true));l.setUint8(0x274,active);l.setUint8(0x290,mode);l.setFloat32(0x260,0.5,true);l.setInt32(8,12,true);l.setInt32(0xc,13,true);if(!missing)v.setBigUint64(0xf88,1n,true);
 const before=hex(enemy),laserBefore=hex(laser);controlEclLaser(enemy,{opcode,args},{operands,gameEnvironment:environment,laserBindings:new Map([[1n,{v:l}]]),atan2:()=>0.875});cases.push({opcode,args:hex(args),missing,before,laserBefore,after:hex(enemy),laserAfter:hex(laser),rng:{seed:rng.seed,count:rng.count}});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1402be065,end=0x1402be065)
    for index,c in enumerate(cases):
        state=bytearray.fromhex(c['before']);struct.pack_into('<Q',state,0xf88,0 if c['missing']else n.manager);m.mem_write(n.owner,bytes(state));m.mem_write(n.manager,bytes.fromhex(c['laserBefore']));m.mem_write(n.assets,bytes(12)+bytes.fromhex(c['args']));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R13,n.owner+0x40),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1),(UC_X86_REG_XMM8,0),(UC_X86_REG_XMM13,int.from_bytes(struct.pack('<f',1.5707963705062866),'little'))]:m.reg_write(reg,value)
        m.emu_start({88:0x140026f52,89:0x140026f97,90:0x140027019,91:0x140027074,92:0x14002709e}[c['opcode']],0x140025d7d,count=100000);actual=bytearray(m.mem_read(n.owner,0x10b0));struct.pack_into('<Q',actual,0xf88,0 if c['missing']else 1);assert actual.hex()==c['after'],(index,'enemy');laser=bytes(m.mem_read(n.manager,0x298));assert laser.hex()==c['laserAfter'],(index,c['opcode'],'laser');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'rng');digest.update(actual+laser)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/ecl-laser-control.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-laser-control-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
