"""ECL post-script motion phase: easing, polar velocity, bounds and completion.

Math thunk inputs are checked; the same supplied trig results are used on both
sides. Native CRT precision, manager position integration and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{advanceEclMotion}from'./shared/th06nc/ecl-motion.mjs';const cases=[],bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.toString('hex');};
for(const mode of [0,1,2,3])for(const ease of [0,1,2,3,4,5,6,7])for(const duration of [1,2,30])for(const clock of [0,1,duration,duration+1])for(const angle of [-1000,-3.2,0,3.2,1000]){
 const enemy=new Uint8Array(0x1100),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);v.setUint8(0xbc,0x80|mode|(ease<<2));v.setInt32(0x260,clock,true);v.setInt32(0x264,duration,true);v.setFloat32(0x22c,angle,true);v.setFloat32(0xc48,0.025,true);v.setFloat32(0x3c,2.5,true);v.setFloat32(0xf78,-0.125,true);
 for(const [base,row]of [[0xb0,[12,34,-2]],[0x244,[18,-6,3]],[0x250,[4,16,1]]])row.forEach((x,i)=>v.setFloat32(base+i*4,x,true));
 const before=Buffer.from(enemy).toString('hex'),trig=[],service=name=>(...args)=>{const result=Math.fround(Math[name](...args));trig.push({name,args:args.map(bits),result:bits(result)});return result;};advanceEclMotion(enemy,{sin:service('sin'),cos:service('cos'),atan2:service('atan2')});cases.push({before,after:Buffer.from(enemy).toString('hex'),trig});
}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();events=[]
    def xmm(reg):return m.reg_read(reg).to_bytes(16,'little')[:4].hex()
    def hook(m,a,size,u):
        if a not in [0x1402be065,0x1402be071,0x1402be07d]:return
        expected=events.pop(0);name={0x1402be065:'atan2',0x1402be071:'cos',0x1402be07d:'sin'}[a];args=[xmm(UC_X86_REG_XMM0)]
        if name=='atan2':args.append(xmm(UC_X86_REG_XMM1))
        assert dict(name=name,args=args)==dict(name=expected['name'],args=expected['args']),(name,args,expected)
        m.reg_write(UC_X86_REG_XMM0,int.from_bytes(bytes.fromhex(expected['result']),'little'));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));events[:]=c['trig']
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R12,0),(UC_X86_REG_XMM8,0),*[(r,int.from_bytes(struct.pack('<f',x),'little'))for r,x in [(UC_X86_REG_XMM9,3.1415927410125732),(UC_X86_REG_XMM10,6.2831854820251465),(UC_X86_REG_XMM11,-3.1415927410125732),(UC_X86_REG_XMM12,-6.2831854820251465)]]]:m.reg_write(reg,value)
        m.emu_start(0x140028840,0x140028a7d,count=100000);assert not events,index
        actual=bytes(m.mem_read(n.owner,0x1100));wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/ecl-motion.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ecl-motion-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
