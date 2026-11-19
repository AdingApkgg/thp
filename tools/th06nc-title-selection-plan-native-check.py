"""State-8 load/unload call plan, observed with successful resource API stubs.

Validates threshold, resource arguments/order and background choice, not actual
texture loading or release, failure cleanup, Spell-specific setup or gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_RIP


def main():
    n=Native();m=n.m;unload=[];resources=[];background=[]
    def hook(m,address,size,user):
        if address in [0x14004ad10,0x14004cbe6]:m.emu_stop();return
        if address not in [0x140002800,0x140007620,0x1400020b0]:return
        slot=m.reg_read(UC_X86_REG_RDX)&0xffffffff
        if address==0x140002800:unload.append(slot)
        else:
            name=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),128)).split(b'\0')[0].decode()
            if address==0x140007620:background.append(name)
            else:resources.append(dict(file=name.split('/')[-1],slot=slot,base=m.reg_read(UC_X86_REG_R9)&0xffffffff))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook);cases=[]
    for frame in [49,50,51]:
     for practice in [0,1]:
      for spell in [0,1]:
       for difficulty in [1,4]:
        state=dict(frame=frame,practice=practice,spell=spell,difficulty=difficulty);unload.clear();resources.clear();background.clear();m.mem_write(n.owner,bytes(0x20000));m.mem_write(n.owner+0x9638,struct.pack('<i',frame));m.mem_write(n.owner+0x168d1,bytes([practice]));m.mem_write(n.owner+0x168d3,bytes([spell]));m.mem_write(n.owner+0x16830,b'\1');m.mem_write(0x1404f27c0,struct.pack('<i',difficulty))
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x14004aab0,n.stack,count=100000)
        expected=None if frame<50 else dict(backgroundEnabled=bool(m.mem_read(n.owner+0x16830,1)[0]),unload=unload.copy(),resources=resources.copy(),background=background[0])
        if frame<50:assert not unload and not resources and not background
        cases.append(dict(state=state,expected=expected))
    path=ROOT/'artifacts/th06nc/title-selection-plan-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{selectionLoadPlan}from'./shared/th06nc/title-selection-layout.mjs';for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-selection-plan-native-cases.json')).entries())assert.deepEqual(selectionLoadPlan(c.state),c.expected,`case ${index}`);console.log('24 selection load plans agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-selection-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-selection-plan-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
