"""Title base backdrop draw call order, temporary writes and addColor controls.

Draw and addColor API entries are observed/stubbed. No GPU/pixel acceptance.
"""
import hashlib,importlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_R12,UC_X86_REG_RSP,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_RIP,UC_X86_REG_XMM7,UC_X86_REG_XMM8
ROOT=Path(__file__).resolve().parents[1]
OFFSETS=[0x16170,0x16290,0x163b0,0x164d0,0x165f0,0x16710]


def main():
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes());blob=Path(target['executable']).read_bytes();assert hashlib.sha256(blob).hexdigest()==target['sha256']
    m=Uc(UC_ARCH_X86,UC_MODE_64);m.mem_map(0x140000000,0xd00000)
    for s in importlib.import_module('th-disasm').sections(blob):m.mem_write(0x140000000+s['va'],blob[s['raw']:s['raw']+s['rawsize']])
    owner,stack=0x70000000,0x71000000;m.mem_map(owner,0x20000);m.mem_map(stack,0x10000)
    calls=[];bright=[61,127,255]
    def hook(m,address,size,user):
        if address not in [0x1400036c0,0x140083c10,0x1400956d0]:return
        values=[m.reg_read(r) for r in [UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8]]
        if address==0x140083c10:
            for ptr,value in zip(values,bright):m.mem_write(ptr,struct.pack('<I',value))
        elif address==0x1400956d0:bright[:]=[v&0xffffffff for v in values]
        else:
            ptr=values[1];state=bytes(m.mem_read(ptr,288));calls.append(dict(offset=ptr-owner,snap=bool(values[2]&255),scaleBits=struct.unpack_from('<I',state,0xe8)[0],color=struct.unpack_from('<I',state,0xec)[0],addColor=bright.copy()))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook);cases=[]
    for mask in range(32):
        for scale in [0.5,0.66,0.8]:
            states=[];m.mem_write(owner,bytes(0x20000))
            for i,p in enumerate(OFFSETS):
                state=bytearray(288);struct.pack_into('<f',state,0xe4,scale);struct.pack_into('<f',state,0xe8,0.75+i*0.125)
                alpha=173 if (mask>>([0,0,1,2,3,4][i]))&1 else 0
                struct.pack_into('<I',state,0xec,(alpha<<24)|0x537fa1);states.append(state.hex());m.mem_write(owner+p,bytes(state))
            before=bytes(m.mem_read(owner,0x20000));calls.clear();bright[:]=[61,127,255]
            for reg,value in [(UC_X86_REG_RSI,owner),(UC_X86_REG_R12,0),(UC_X86_REG_RSP,stack+0x8000),(UC_X86_REG_XMM7,0x3f800000),(UC_X86_REG_XMM8,0)]:m.reg_write(reg,value)
            m.emu_start(0x14005499e,0x140054bcc,count=100000)
            assert bytes(m.mem_read(owner,0x20000))==before,'native leaked temporary VM writes'
            assert bright==[61,127,255]
            cases.append(dict(states=states,expected=calls.copy()))
    home=ROOT/'artifacts/th06nc';path=home/'title-backdrop-draw-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{drawTitleBackdropBase}from'./shared/th06nc/title-backdrop-draw.mjs';
const offsets=[0x16170,0x16290,0x163b0,0x164d0,0x165f0,0x16710];
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-backdrop-draw-native-cases.json')).entries()){
const slots=new Map(offsets.map((p,i)=>{const state=Buffer.from(c.states[i],'hex');return[p,{state,v:new DataView(state.buffer,state.byteOffset,state.byteLength)}]})),actual=[];
drawTitleBackdropBase({slots},(vm,options)=>actual.push({offset:[...slots].find(([p,v])=>v===vm)[0],snap:options.snap,scaleBits:vm.v.getUint32(0xe8,true),color:vm.v.getUint32(0xec,true),addColor:options.addColor}),{addColor:[61,127,255]});assert.deepEqual(actual,c.expected,`case ${index}`);assert.deepEqual([...slots.values()].map(v=>v.state.toString('hex')),c.states);}
console.log('96 native backdrop draw plans agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),drawCalls=sum(len(c['expected']) for c in cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-backdrop-draw.mjs').read_bytes()).hexdigest(),executableSha256=target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-backdrop-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
