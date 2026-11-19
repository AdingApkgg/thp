"""ECL assignment helper, original x64 including source/destination side effects.

The atan2 thunk is supplied the same fixed result in both implementations;
CRT trigonometric precision and ECL dispatch/gameplay are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP,UC_X86_REG_RIP,UC_X86_REG_RAX,UC_X86_REG_XMM0,UC_X86_REG_R8

def main():
    script="""
import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const cases=[],bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.toString('hex');};
const ids=[...Array.from({length:25},(_,i)=>-10001-i),-10101,-10100,-10102,-9999,0,42],raws=[...ids,0x43700000,0xc61c4533];
for(const destination of ids)for(const input of raws){
const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);
const environment={difficulty:3,playerPosition:[32,-16,8],character:1,shot:0,rng:new NativeRng(0xbeef,99),atan2:()=>0.875},resolver=new EclOperands(enemy,environment),before=Buffer.from(enemy).toString('hex');resolver.assign(destination,input);
const word=Buffer.alloc(4);word.writeUInt32LE(input>>>0);cases.push({destination,seed:0xbeef,count:99,input:word.toString('hex'),coincident:false,before,after:Buffer.from(enemy).toString('hex'),scratch:Buffer.from(resolver.scratch).toString('hex'),rng:{seed:environment.rng.seed,count:environment.rng.count}});}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a!=0x1402be065:return
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',0.875),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets,bytes.fromhex(c['input']));m.mem_write(0x1404f27c0,struct.pack('<i',3));m.mem_write(0x1404f1e80,b'\1\0');m.mem_write(0x140506ad0,struct.pack('<3f',*([0,1,2]if c['coincident']else[32,-16,8])));m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']))
        for address in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]:m.mem_write(address,bytes(4))
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,c['destination']&0xffffffff);m.reg_write(UC_X86_REG_R8,n.assets);m.emu_start(0x14002e620,n.stack+0xf000,count=10000)
        actual=bytes.fromhex(c['input'])
        enemy=bytes(m.mem_read(n.owner,0x1100));assert enemy.hex()==c['after'],index
        scratch=b''.join(bytes(m.mem_read(a,4))for a in [0x140a6eb98,0x140a6ebb8,0x140a6ebbc]);assert scratch.hex()==c['scratch'],(index,scratch.hex(),c['scratch'])
        count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],index;digest.update(actual+enemy+scratch)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/ecl-operands.mjs','shared/th06nc/rng.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-assignment-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
