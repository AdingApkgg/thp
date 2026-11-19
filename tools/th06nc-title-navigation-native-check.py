"""Original generic menu navigation and queued cursor sound, no audio output.

Repeat-trigger generation, disabled-item skipping and owner transitions excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSP


def main():
    n=Native();m=n.m;cases=[]
    for count in [1,9,10]:
      for selection in [-1,0,9,10]:
       for held in [0,0x10,0x20,0x30]:
        for previous in [0,0x10,0x20,0x30]:
         for repeat in [0,1]:
          for disabled in [False,True]:
           for slots in [[-1,-1,-1],[12,-1,2],[3,4,5],[3,-1,12]]:
            m.mem_write(n.owner+0x28,struct.pack('<i',selection));m.mem_write(0x140a6ec60,struct.pack('<II',held,previous));m.mem_write(0x140a6ec48,struct.pack('<i',repeat))
            m.mem_write(0x140509694,bytes([disabled]));m.mem_write(0x140509670,struct.pack('<3i',*slots))
            sp=n.stack+0x8008;m.mem_write(sp,struct.pack('<Q',n.stack))
            for reg,value in [(UC_X86_REG_RCX,n.owner),(UC_X86_REG_RDX,count),(UC_X86_REG_RSP,sp)]:m.reg_write(reg,value)
            m.emu_start(0x14004d1f0,n.stack,count=10000);assert m.reg_read(UC_X86_REG_RSP)==sp+8
            ret=m.reg_read(UC_X86_REG_RAX)&0xffffffff;ret=ret-0x100000000 if ret>=0x80000000 else ret
            cases.append(dict(selection=selection,count=count,keys=dict(held=held,previous=previous,repeat=repeat),sound=dict(disabled=disabled,slots=slots),expected=dict(selection=struct.unpack('<i',m.mem_read(n.owner+0x28,4))[0],direction=ret,soundSlots=list(struct.unpack('<3i',m.mem_read(0x140509670,12))))))
    path=ROOT/'artifacts/th06nc/title-navigation-native-cases.json';path.write_text(json.dumps(cases),encoding='utf-8')
    script="""
import{readFileSync}from'node:fs';import assert from'node:assert/strict';import{navigateTitle}from'./shared/th06nc/title-navigation.mjs';
for(const [index,c]of JSON.parse(readFileSync('artifacts/th06nc/title-navigation-native-cases.json')).entries())assert.deepEqual(navigateTitle(c.selection,c.count,c.keys,c.sound),c.expected,`case ${index}`);
console.log('3072 native navigation cases agree');
"""
    subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
    report=dict(scope=__doc__,cases=len(cases),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-navigation.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-navigation-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
