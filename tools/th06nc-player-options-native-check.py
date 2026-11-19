"""Player option spread/focus transitions 694f6..696f4, including reversals.

Full player owner bytes compared. Input/fire processing, ANM and shots excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-options.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{advancePlayerOptions}from'./shared/th06nc/player-options.mjs';const cases=[];for(let mode=0;mode<5;mode++)for(const clock of [0,1,2,4,7,8,9])for(const focus of [false,true])for(const power of [0,7,8,128]){const state=new Uint8Array(0xa300),v=new DataView(state.buffer);v.setUint8(0x79f8,mode);v.setInt32(0x404,clock,true);v.setInt32(0x400,-123,true);v.setUint8(0x785c,Number(focus));for(const p of [0x7880,0x788c])v.setFloat32(p,100,true);for(const p of [0x7884,0x7890])v.setFloat32(p,200,true);advancePlayerOptions(state,{power});cases.push({mode,clock,focus,power,sha256:createHash('sha256').update(state).digest('hex'),state:Buffer.from(state).toString('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(cases):
        state=bytearray(0xa300);state[0x79f8]=c['mode'];state[0x785c]=c['focus'];struct.pack_into('<2i',state,0x400,-123,c['clock'])
        for p in [0x7880,0x788c]:struct.pack_into('<f',state,p,100)
        for p in [0x7884,0x7890]:struct.pack_into('<f',state,p,200)
        m.mem_write(n.owner,bytes(state));m.mem_write(0x1404f1e88,struct.pack('<H',c['power']))
        for reg,value in [(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R15D,8),(UC_X86_REG_R12D,1),(UC_X86_REG_ESI,0),(UC_X86_REG_R9,n.owner+0x79f8)]:m.reg_write(reg,value)
        m.reg_write(UC_X86_REG_XMM1,0);m.reg_write(UC_X86_REG_XMM2,0);m.emu_start(0x1400694f6,0x1400696f4,count=10000);actual=bytes(m.mem_read(n.owner,0xa300));wanted=bytes.fromhex(c['state']);assert actual==wanted,(index,c['mode'],c['clock'],c['focus'],c['power'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:20]);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-options-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
