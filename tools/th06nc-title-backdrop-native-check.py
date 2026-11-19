"""Original title backdrop transition helpers with ANM update calls observed.

ANM update entry is replaced with a no-op to isolate owner scheduling and scale
overrides. Actual animation VM behavior has its own independent checks.
"""
import hashlib,importlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP,UC_X86_REG_RIP
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=[0x16170,0x16290,0x163b0,0x164d0,0x165f0,0x16710]


def main():
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());blob=Path(target['executable']).read_bytes();assert hashlib.sha256(blob).hexdigest()==target['sha256']
    m=Uc(UC_ARCH_X86,UC_MODE_64);m.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(blob):m.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    owner,stack=0x70000000,0x71000000;m.mem_map(owner,0x20000);m.mem_map(stack,0x10000)
    calls=[]
    def hook(m,address,size,user):
        if address!=0x1400069b0:return
        calls.append(m.reg_read(UC_X86_REG_RDX)-owner)
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RIP,ret);m.reg_write(UC_X86_REG_RAX,0)
    m.hook_add(UC_HOOK_CODE,hook)
    def run(address):
        sp=stack+0x8008;m.mem_write(sp,struct.pack('<Q',stack));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(address,stack,count=100000);assert m.reg_read(UC_X86_REG_RSP)==sp+8
    def snapshot():return dict(control=bytes(m.mem_read(owner+0x16834,40)).hex(),counter=struct.unpack('<i',m.mem_read(owner+0x16868,4))[0],vms=[bytes(m.mem_read(owner+p,288)).hex() for p in OFFSETS])
    cases=[]
    for busy in [0,1,2]:
        for request in range(1,8):
            m.mem_write(owner,bytes(0x20000));m.mem_write(owner+0x16868,struct.pack('<i',99))
            if busy==1:m.mem_write(owner+0x16834,b'\1')
            if busy==2:m.mem_write(owner+0x163b0+0x86,struct.pack('<h',3))
            for i,p in enumerate(OFFSETS):
                m.mem_write(owner+p+0xe4,struct.pack('<f',1+i*0.125));m.mem_write(owner+p+0xe8,struct.pack('<f',1+i*0.125))
            initial=snapshot();m.reg_write(UC_X86_REG_RDX,request);run(0x140047080);after=snapshot();frames=[]
            for tick in range(70):
                calls.clear();run(0x140046ef0);assert calls==OFFSETS;frames.append(snapshot())
            cases.append(dict(initial=initial,request=request,after=after,frames=frames))
    home=ROOT/'artifacts/th06nc';home.mkdir(parents=True,exist_ok=True);path=home/'title-backdrop-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{TitleBackdrop}from'./shared/th06nc/title-backdrop.mjs';
const offsets=[0x16170,0x16290,0x163b0,0x164d0,0x165f0,0x16710];
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-backdrop-native-cases.json')).entries()){
const slots=new Map(offsets.map((p,i)=>{const state=Buffer.from(c.initial.vms[i],'hex'),v=new DataView(state.buffer,state.byteOffset,state.byteLength);return[p,{state,v,interrupt(id){v.setInt16(0x8a,id,true)},tick(){}}]}));
const b=new TitleBackdrop({slots});b.control.set(Buffer.from(c.initial.control,'hex'));b.counter=c.initial.counter;
const snap=()=>({control:Buffer.from(b.control).toString('hex'),counter:b.counter,vms:b.vms.map(vm=>Buffer.from(vm.state).toString('hex'))});
b.request(c.request);assert.deepEqual(snap(),c.after,`request ${index}`);for(const [tick,f]of c.frames.entries()){b.tick();assert.deepEqual(snap(),f,`case ${index} tick ${tick}`);}}
console.log('21 requests and 1470 backdrop updates agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),ticks=len(cases)*70,sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-backdrop.mjs').read_bytes()).hexdigest(),executableSha256=target['sha256'],casesSha256=hashlib.sha256(path.read_bytes()).hexdigest(),passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-backdrop-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
