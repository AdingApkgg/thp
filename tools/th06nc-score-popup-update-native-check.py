"""Priority-1 popup motion/expiry, original 90d0, all 515 slots.

UI replacement callbacks are controlled services. Full popup storage checked
at signed timer boundaries, inactive slots and all UI suspension combinations.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/score-popup-update.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';import{advanceScorePopups}from'./shared/th06nc/score-popup-update.mjs';const cases=[];for(let flags=0;flags<8;flags++)for(const frame of [-999,-1,0,59,60,61,2147483647])for(const alternate of [false,true]){const pool=new ScorePopupPool(),v=new DataView(pool.storage.buffer);for(let slot=0;slot<515;slot++){const p=slot*40;v.setInt32(p,-99,true);v.setInt32(p+4,frame,true);v.setFloat32(p+0x14,slot*.125,true);v.setUint8(p+0x1c,!alternate||slot%2?1:0);}advanceScorePopups(pool,{suspended:flags!==0});cases.push({flags,frame,alternate,sha256:createHash('sha256').update(pool.storage).digest('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000a120,0x14000b4f0,0x14000c230]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        initial=bytearray(515*40)
        for slot in range(515):
            p=slot*40;struct.pack_into('<ii',initial,p,-99,c['frame']);struct.pack_into('<f',initial,p+0x14,slot*.125);initial[p+0x1c]=int(not c['alternate']or slot%2!=0)
        m.mem_write(0x1403de870,bytes(initial))
        for bit,a in enumerate([0x1404f27b0,0x1404f27b1,0x1404f27b6]):m.mem_write(a,bytes([bool(c['flags']&(1<<bit))]))
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,0x1403de620);m.emu_start(0x1400090d0,n.stack+0xf000,count=1000000);actual=bytes(m.mem_read(0x1403de870,len(initial)));assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,c);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-popup-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
