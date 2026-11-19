"""Original sampled-key repeat phase versus portable input over key sequences.

Starts after physical polling; keyboard/gamepad mapping and owner transitions
are not covered. No game process or audible device is started.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RBX


def main():
    n=Native();m=n.m
    sequences=[[0]*100,[0x10]*1000,[0x20]*1000,[0x30]*1000,[0x10,0x20]*100,[0x10]*70+[0x110]*70+[0x10]*70,[0]*40+[0x20]*80+[0]*40+[0x20]*80]
    cases=[]
    for seq in sequences:
        held=0;m.mem_write(0x140a6ec5c,bytes(4));frames=[]
        for new in seq:
            m.mem_write(0x140a6ec64,struct.pack('<I',held));m.reg_write(UC_X86_REG_RAX,new);m.reg_write(UC_X86_REG_RBX,0)
            m.emu_start(0x140079d37,0x140079d7a,count=10000)
            repeat=struct.unpack('<I',m.mem_read(0x140a6ec48,4))[0];clock=struct.unpack('<I',m.mem_read(0x140a6ec5c,4))[0]
            frames.append(dict(keys=dict(held=new,previous=held,repeat=repeat),clock=clock));held=new
        cases.append(dict(sequence=seq,frames=frames))
    path=ROOT/'artifacts/th06nc/title-input-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{TitleInput}from'./shared/th06nc/title-navigation.mjs';
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-input-native-cases.json')).entries()){const input=new TitleInput();for(const [tick,held]of c.sequence.entries()){assert.deepEqual(input.sample(held),c.frames[tick].keys,`sequence ${index} tick ${tick}`);assert.equal(input.clock,c.frames[tick].clock);}}
console.log('All sampled input sequences agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,sequences=len(cases),ticks=sum(len(c['frames']) for c in cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-navigation.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-input-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
