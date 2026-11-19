"""All nine ordinary bullet emission patterns, native fa57..fdf9.

Compares speed, normalized angle and shared RNG. Pool allocation, ANM,
movement, collisions and complete gameplay are outside this focused check.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/bullet-pattern.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{bulletPattern}from'./shared/th06nc/bullet-pattern.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[];
for(let mode=0;mode<9;mode++)for(const ways of [1,2,5,6])for(const layers of [1,3])for(let way=0;way<ways;way++)for(let layer=0;layer<layers;layer++)for(const base of [-150,0.5,150]){
 const descriptor=new Uint8Array(108),v=new DataView(descriptor.buffer);v.setInt16(0x18,ways,true);v.setInt16(0x1a,layers,true);v.setUint16(0x30,mode,true);v.setFloat32(0x34,base,true);v.setFloat32(0x38,0.6,true);v.setFloat32(4,3.7,true);v.setFloat32(8,0.4,true);const rng=new NativeRng(0x8abc,7),aim=Math.fround(1.2),result=bulletPattern(descriptor,way,layer,{aim,rng});cases.push({descriptor:Buffer.from(descriptor).toString('hex'),way,layer,aim,result,seed:rng.seed,count:rng.count});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def xmm(reg,value):m.reg_write(reg,int.from_bytes(struct.pack('<f',value),'little'))
    for index,c in enumerate(cases):
        m.mem_write(n.vm,bytes(0x620));m.mem_write(n.owner,bytes.fromhex(c['descriptor']));m.mem_write(0x140a6ec40,struct.pack('<IH',7,0x8abc))
        for reg,value in [(UC_X86_REG_RBX,n.vm),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBP,0),(UC_X86_REG_R13D,c['way']),(UC_X86_REG_R8D,c['layer']),(UC_X86_REG_R9,0x140000000),(UC_X86_REG_R11D,0x9630),(UC_X86_REG_R14D,0x6553),(UC_X86_REG_R10D,1)]:m.reg_write(reg,value)
        for reg,value in [(UC_X86_REG_XMM4,c['aim']),(UC_X86_REG_XMM5,2**-32),(UC_X86_REG_XMM6,-1),(UC_X86_REG_XMM11,struct.unpack('<f',struct.pack('<f',3.141592653589793))[0]),(UC_X86_REG_XMM12,struct.unpack('<f',struct.pack('<f',-3.141592653589793))[0]),(UC_X86_REG_XMM13,0),(UC_X86_REG_XMM14,struct.unpack('<f',struct.pack('<f',6.283185307179586))[0]),(UC_X86_REG_XMM15,struct.unpack('<f',struct.pack('<f',-6.283185307179586))[0])]:xmm(reg,value)
        m.emu_start(0x14000fa57,0x14000fdf9,count=10000)
        actual=bytes(m.mem_read(n.vm+0x24,4))+bytes(m.mem_read(n.vm+0x40,4))+bytes(m.mem_read(0x140a6ec40,6));wanted=struct.pack('<ffIH',c['result']['speed'],c['result']['angle'],c['count'],c['seed'])
        assert actual==wanted,(index,c,struct.unpack('<ffIH',actual),struct.unpack('<ffIH',wanted));digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),modes=9,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-bullet-pattern-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
