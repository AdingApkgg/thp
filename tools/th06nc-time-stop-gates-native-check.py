"""Original time-stop task gates, before any ordinary update or pointer use.

Player/projectile/background/HUD-message owners are filled with sentinel bytes.
For flag 1/255, complete owners remain unchanged except STD cover color 1bc.
This establishes native gate semantics; StageWorld ordering is covered by the
separate controlled stage-five combat comparison, not by this native-only check.
"""
import hashlib,json,struct
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    n=Native();m=n.m;digest=hashlib.sha256();cases=0
    for flag in [1,255]:
        m.mem_write(0x1404f27b9,bytes([flag]))
        for entry,base,size in [(0x140068820,0x1404ff3a0,0xa2b8),(0x140010870,0x1403ec2a0,0xff61c),(0x140077bb0,0x140509b60,0x220),(0x14003cc50,n.owner,0x4000)]:
            before=bytes((i*17+9)&255 for i in range(size));m.mem_write(base,before);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,base);m.emu_start(entry,n.assets,count=10000);actual=bytes(m.mem_read(base,size));wanted=bytearray(before)
            if entry==0x140077bb0:struct.pack_into('<I',wanted,0x1bc,0x60803030)
            assert actual==wanted,(hex(entry),flag,[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);digest.update(actual);cases+=1
    report=dict(scope=__doc__,cases=cases,stateSha256=digest.hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-time-stop-gates-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
