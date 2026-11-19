"""Stable state-3 menu draw order, offsets and state restoration.

Draw entry is observed without GPU execution. Menu slide and other states excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_R12,UC_X86_REG_RSP,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_RIP,UC_X86_REG_XMM5,UC_X86_REG_XMM9


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{drawStableTitleMain}from'./shared/th06nc/title-main-draw.mjs';
const group=new TitleAnimations(new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])));
for(const vm of group.slots.values()){vm.v.setFloat32(0x18,0.125,true);vm.v.setFloat32(0x1c,-0.25,true);vm.v.setFloat32(0x20,0.5,true);}
const states=[...group.slots].map(([offset,v])=>({offset,state:Buffer.from(v.state).toString('hex')})),cases=[];
for(const mask of [0,7]){const disabled=Uint8Array.from({length:173},(_,i)=>mask&&i%mask===0?1:0),calls=[];drawStableTitleMain(group,(vm,options)=>calls.push({offset:[...group.slots].find(([p,v])=>v===vm)[0],snap:options.snap,position:Buffer.from(vm.state.slice(0xc8,0xd4)).toString('hex')}),{disabled});cases.push({disabled:Array.from(disabled),calls});}console.log(JSON.stringify({refs:titleResources,states,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;calls=[]
    def hook(m,address,size,user):
        if address!=0x1400036c0:return
        ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(offset=ptr-n.owner,snap=bool(m.reg_read(UC_X86_REG_R8)&255),position=bytes(m.mem_read(ptr+0xc8,12)).hex()))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook)
    for c in data['cases']:
        m.mem_write(n.owner,bytes(0x20000));m.mem_write(n.owner+0x168b0,struct.pack('<i',3));m.mem_write(n.owner+0x158e0,bytes(c['disabled']))
        for slot in data['states']:
            state=bytearray.fromhex(slot['state']);ptr=struct.unpack_from('<Q',state,0x100)[0]
            if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
            m.mem_write(n.owner+slot['offset'],bytes(state))
        initial=bytes(m.mem_read(n.owner,0x20000));calls.clear()
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_R12,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_XMM5,0),(UC_X86_REG_XMM9,0)]:m.reg_write(reg,value)
        m.emu_start(0x140054f96,0x1400551ef,count=100000)
        assert calls==c['calls'],(len(calls),len(c['calls']))
        assert bytes(m.mem_read(n.owner,0x20000))==initial,'native draw changed persistent owner state'
    report=dict(scope=__doc__,cases=len(data['cases']),drawCalls=sum(len(c['calls']) for c in data['cases']),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-main-draw.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-main-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
