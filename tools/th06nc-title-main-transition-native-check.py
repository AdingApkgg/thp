"""Native state-3 confirmation/cancellation decision phase versus portable code.

Fade/audio API calls are observed, not executed. Destination menu owners,
gameplay launch, score unlock decoding, navigation and draw are outside scope.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RIP


def main():
    n=Native();m=n.m;effects=[]
    def hook(m,address,size,user):
        if address in [0x140049ab6,0x140047f60,0x14004cbf4]:m.emu_stop();return
        if address not in [0x140076050,0x140076af0]:return
        edx=m.reg_read(UC_X86_REG_RDX)&0xffffffff
        effects.append(dict(kind='fade',mode=m.reg_read(UC_X86_REG_RCX)&0xffffffff,frames=edx) if address==0x140076050 else dict(kind='sound',id=edx))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook);cases=[]
    # Twelve clear-marker bytes probed by the original Extra gate.
    scores=[0x4ff101,0x4ff102,0x4ff103,0x4ff119,0x4ff11a,0x4ff11b,0x4ff131,0x4ff132,0x4ff133,0x4ff149,0x4ff14a,0x4ff14b]
    for selection in range(10):
     for held in [0,0x100,0x800,0x200,0x900,0xb00,0x300]:
      for extra in [False,True]:
       for frame in [19,20,21]:
        initial=dict(selection=selection,state=3,frame=frame,pulse=123,practice=1,spell=1,difficulty=5,configuredDifficulty=5)
        m.mem_write(n.owner,bytes(0x20000))
        for p,key in [(0x28,'selection'),(0x30,'pulse'),(0x9638,'frame'),(0x168b0,'state')]:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
        m.mem_write(n.owner+0x168d1,b'\1');m.mem_write(n.owner+0x168d3,b'\1');m.mem_write(0x1404f27c0,struct.pack('<i',5));m.mem_write(0x140c21db9,b'\5')
        for address in scores:m.mem_write(0x140000000+address,bytes([99 if extra else 0]))
        m.mem_write(0x140a6ec60,struct.pack('<II',held,0));effects.clear()
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x14004832d,n.stack,count=100000)
        actual=dict(initial)
        for p,key in [(0x28,'selection'),(0x30,'pulse'),(0x9638,'frame'),(0x168b0,'state')]:actual[key]=struct.unpack('<i',m.mem_read(n.owner+p,4))[0]
        actual['practice']=m.mem_read(n.owner+0x168d1,1)[0];actual['spell']=m.mem_read(n.owner+0x168d3,1)[0];actual['difficulty']=struct.unpack('<i',m.mem_read(0x1404f27c0,4))[0];actual['configuredDifficulty']=m.mem_read(0x140c21db9,1)[0]
        interrupts=[struct.unpack('<h',m.mem_read(n.owner+0x96ca+i*288,2))[0] for i in range(173)]
        assert len(set(interrupts))==1
        cases.append(dict(initial=initial,keys=dict(held=held,previous=0),extra=extra,expected=dict(state=actual,effects=effects.copy(),interrupt=interrupts[0] or None)))
    path=ROOT/'artifacts/th06nc/title-main-transition-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{transitionTitleMain}from'./shared/th06nc/title-main-transition.mjs';
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-main-transition-native-cases.json')).entries())assert.deepEqual(transitionTitleMain(c.initial,c.keys,{extraAvailable:c.extra}),c.expected,`case ${index}`);console.log('420 native main-menu transition cases agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-main-transition.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-main-transition-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
