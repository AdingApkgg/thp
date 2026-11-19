"""Player input selection, native 69066..69241/69273.

All 256 low input combinations, focus and supplied normal/diagonal speeds.
Movement integration, animation changes, shots and player lifecycle excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-input.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{playerInputVelocity}from'./shared/th06nc/player-input.mjs';const cases=[];for(let input=0;input<256;input++)for(const speeds of [[4,2,Math.fround(4/Math.SQRT2),Math.fround(2/Math.SQRT2)],[5,2.5,3.5,1.75],[0,0,0,0],[1.25,0.625,0.875,0.4375]]){const[speed,focusSpeed,diagonalSpeed,diagonalFocusSpeed]=speeds;const result=playerInputVelocity(input,{speed,focusSpeed,diagonalSpeed,diagonalFocusSpeed}),b=Buffer.alloc(13);b.writeInt32LE(result.direction);b.writeUInt8(Number(result.focus),4);b.writeFloatLE(result.x,5);b.writeFloatLE(result.y,9);cases.push({input,speeds,result,expected:b.toString('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
    def stop(m,a,size,u):m.emu_stop()
    for a in [0x140069241,0x140069273]:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
    digest=hashlib.sha256()
    for index,c in enumerate(cases):
        m.mem_write(n.owner+0x7860,struct.pack('<4f',*c['speeds']))
        for reg,value in [(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R11D,c['input']),(UC_X86_REG_R12D,1),(UC_X86_REG_R15D,8),(UC_X86_REG_R8D,5),(UC_X86_REG_EBX,2),(UC_X86_REG_ESI,0)]:m.reg_write(reg,value)
        m.emu_start(0x140069066,0x140069291,count=10000)
        actual=bytes(m.mem_read(n.owner+0x7750,4))+bytes(m.mem_read(n.owner+0x785c,1))+m.reg_read(UC_X86_REG_XMM6).to_bytes(16,'little')[:4]+m.reg_read(UC_X86_REG_XMM7).to_bytes(16,'little')[:4];r=c['result'];wanted=bytes.fromhex(c['expected'])
        assert actual==wanted,(index,c,actual.hex(),wanted.hex());digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-input-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
