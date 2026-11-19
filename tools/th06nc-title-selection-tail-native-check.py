"""Base state-8 owner tail, pending animation labels and fade-object request.

No Spell path, texture release/loading, frame delivery, drawing or gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP


def main():
    n=Native();m=n.m;fade=0x75000000;m.mem_map(fade,0x1000);cases=[]
    for difficulty in [0,3,4,5]:
     for configured in [0,2,4]:
      for fast in [False,True]:
       for duration in [0,60]:
        initial=dict(state=8,frame=50,totalFrame=99,pulse=33,backgroundEnabled=False,spell=0,difficulty=difficulty,configuredDifficulty=configured,fastEntry=fast,menuFadeDuration=duration)
        m.mem_write(n.owner,bytes(0x20000));m.mem_write(fade,bytes(0x1000));m.mem_write(0x140c22158,struct.pack('<Q',fade));m.mem_write(0x1404f27c0,struct.pack('<i',difficulty));m.mem_write(0x140c21db9,bytes([configured]));m.mem_write(n.owner+0x168d0,bytes([fast]));m.mem_write(n.owner+0x168a8,struct.pack('<i',duration))
        for p,value in [(0x168b0,8),(0x9638,50),(0x2c,99),(0x30,33)]:m.mem_write(n.owner+p,struct.pack('<i',value))
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x14004afb9,0x14004b0c6,count=100000)
        actual=dict(initial)
        for p,key in [(0x168b0,'state'),(0x9638,'frame'),(0x2c,'totalFrame'),(0x30,'pulse'),(0x28,'selection'),(0x168ac,'menuFadePreviousDuration'),(0x168a8,'menuFadeDuration'),(0,'menuFadeTicks'),(0x18,'menuFadeStartColor')]:actual[key]=struct.unpack('<i',m.mem_read(n.owner+p,4))[0]
        effects=[]
        if not fast:
            assert struct.unpack('<i',m.mem_read(fade+4,4))[0]==-999
            assert struct.unpack('<i',m.mem_read(fade+8,4))[0]==0
            assert struct.unpack('<i',m.mem_read(fade+0x20,4))[0]==0
            effects=[dict(kind='entryFade',frames=struct.unpack('<i',m.mem_read(fade,4))[0],alpha=struct.unpack('<i',m.mem_read(fade+0x2c,4))[0],mode=struct.unpack('<i',m.mem_read(fade+0x34,4))[0])]
        else:assert bytes(m.mem_read(fade,0x1000))==bytes(0x1000)
        pending=[struct.unpack('<h',m.mem_read(n.owner+0x96ca+i*288,2))[0] for i in range(173)]
        cases.append(dict(initial=initial,expected=dict(state=actual,effects=effects),pending=pending))
    path=ROOT/'artifacts/th06nc/title-selection-tail-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{finishSelectionEntry}from'./shared/th06nc/title-selection-layout.mjs';
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-selection-tail-native-cases.json')).entries()){
const pending=new Int16Array(173),slots=new Map(Array.from({length:173},(_,i)=>[0x9640+i*288,{interrupt(v){pending[i]=v}}]));assert.deepEqual(finishSelectionEntry({slots},c.initial),c.expected,`case ${index}`);assert.deepEqual(Array.from(pending),c.pending);}
console.log('48 selection owner-tail cases agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-selection-layout.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-selection-tail-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
