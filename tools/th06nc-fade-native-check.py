"""Global fade request and tick functions, all 56 bytes against original x64."""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP

def main():
    script="""
import{NativeFade}from'./shared/th06nc/fade.mjs';const cases=[];
for(const alpha of [0,1,128,254,255])for(const frames of [0,1,2,30,45])for(const incoming of [false,true]){
const fade=new NativeFade();fade.v.setInt32(0x28,alpha,true);const before=Buffer.from(fade.state).toString('hex');if(incoming)fade.requestIn(0xabcdef12,frames);else fade.requestOut(0xabcdef12,frames);const afterRequest=Buffer.from(fade.state).toString('hex'),ticks=[];for(let i=0;i<100;i++){fade.tick();ticks.push(Buffer.from(fade.state).toString('hex'));}cases.push({before,frames,incoming,afterRequest,ticks});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    m.mem_write(0x140c22158,struct.pack('<Q',n.vm))
    def run(addr,cx,dx=0):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,cx);m.reg_write(UC_X86_REG_RDX,dx);m.emu_start(addr,n.stack+0xf000,count=10000)
    for i,c in enumerate(cases):
        m.mem_write(n.vm,bytes.fromhex(c['before']));run(0x140076010 if c['incoming'] else 0x140076050,0xabcdef12,c['frames']);assert bytes(m.mem_read(n.vm,56)).hex()==c['afterRequest'],i
        for t,wanted in enumerate(c['ticks']):
            run(0x140075af0,n.vm);actual=bytes(m.mem_read(n.vm,56));assert actual.hex()==wanted,(i,t,actual.hex(),wanted);digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),ticks=sum(len(c['ticks'])for c in cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/fade.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-fade-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
